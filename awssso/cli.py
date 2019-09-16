import argparse
import os
import sys
import webbrowser
from time import time

import inquirer
from halo import Halo

from awssso import __version__
from awssso.config import Configuration
from awssso.helpers import (SPINNER_MSGS, CredentialsHelper, SecretsManager,
                            config_override, validate_empty, validate_url)
from awssso.saml import AssumeRoleValidationError, BotoClientError, SAMLHelper
from awssso.ssoclient import SSOClient
from awssso.ssodriver import AlertMessage, MFACodeNeeded, SSODriver


def __refresh_token(url, username, password, config_dir, headless=True, spinner=True):
    spinner = Halo(enabled=spinner)
    try:
        spinner.start(SPINNER_MSGS['token_refresh'])
        driver = SSODriver(url, username, headless=headless, cookie_dir=config_dir)
        try:
            return driver.refresh_token(username, password)
        except MFACodeNeeded as e:
            spinner.stop()
            mfacode = inquirer.text(message='MFA Code')
            spinner.start(SPINNER_MSGS['mfa_send'])
            driver.send_mfa(e.mfa_form, mfacode)
            spinner.start(SPINNER_MSGS['token_refresh'])
            return driver.get_token()
        except AlertMessage as e:
            sys.exit(e)
        finally:
            spinner.stop()
    except KeyboardInterrupt as e:
        spinner.stop()
        raise e
    finally:
        driver.close()


def __get_or_refresh_token(url, username, password, secrets, config_dir, force_refresh=False, headless=True, spinner=True):
    token = secrets.get('authn-token')
    stored_password = secrets.get('credentials')
    expiry_date = int(secrets.get('authn-expiry-date', '0'))
    if (force_refresh) or (not token) or (time() > expiry_date) or (stored_password != password):
        token, expiry_date = __refresh_token(url, username, password, config_dir, headless, spinner)
        if stored_password != password:
            secrets.set('credentials', password)
        secrets.set('authn-token', token)
        secrets.set('authn-expiry-date', str(expiry_date))
    return token


def configure(args):
    profile = args.profile
    cfg = Configuration()
    params = config_override(cfg.config, profile, args)

    try:
        inquirer.prompt([
            inquirer.Text('url', message='URL', default=params.get('url', ''), validate=validate_url),
            inquirer.Text('aws_profile', message='AWS CLI profile', default=params.get('aws_profile', profile), validate=validate_empty),
            inquirer.Text('username', message='Username', default=params.get('username', ''), validate=validate_empty)
        ], answers=params, raise_keyboard_interrupt=True)
        secrets = SecretsManager(params.get('username'), params.get('url'))
        password = inquirer.password(message='Password', default=secrets.get('credentials', ''), validate=validate_empty)

        token = __get_or_refresh_token(
            params['url'], params['username'], password,
            secrets, cfg.configdir, args.force_refresh, args.headless, args.spinner
        )
        sso = SSOClient(token, params['region'])

        instances = sso.get_instances()
        inquirer.prompt([
            inquirer.List(
                'instance_id',
                message='AWS Account',
                choices=[(_['name'], _['id']) for _ in instances]
            )
        ], answers=params, raise_keyboard_interrupt=True)

        profiles = sso.get_profiles(params['instance_id'])
        inquirer.prompt([
            inquirer.List(
                'profile_id',
                message='AWS Profile',
                choices=[(_['name'], _['id']) for _ in profiles]
            )
        ], answers=params, raise_keyboard_interrupt=True)

        cfg.save()
    except KeyboardInterrupt:
        sys.exit(1)


def login(args):
    profile = args.profile
    cfg = Configuration()

    if profile not in cfg.config:
        sys.exit(f'profile {profile} does not exist, use "awssso configure -p {profile}" to create it')

    params = config_override(cfg.config, profile, args)
    aws_profile = params.get('aws_profile', profile)
    secrets = SecretsManager(params.get('username'), params.get('url'))
    password = secrets.get('credentials')

    if not password:
        sys.exit(f'Cannot get password from secrets, run "awssso configure -p {profile}"')

    try:
        token = __get_or_refresh_token(
            params['url'], params['username'], password,
            secrets, cfg.configdir, args.force_refresh, args.headless, args.spinner
        )
        sso = SSOClient(token, params['region'])

        if args.interactive:
            instances = sso.get_instances()
            inquirer.prompt([
                inquirer.List(
                    'instance_id',
                    message='AWS Account',
                    choices=[(_['name'], _['id']) for _ in instances]
                )
            ], answers=params, raise_keyboard_interrupt=True)

            profiles = sso.get_profiles(params['instance_id'])
            inquirer.prompt([
                inquirer.List(
                    'profile_id',
                    message='AWS Profile',
                    choices=[(_['name'], _['id']) for _ in profiles]
                )
            ], answers=params, raise_keyboard_interrupt=True)

        payload = sso.get_saml_payload(params['instance_id'], params['profile_id'])
        saml = SAMLHelper(payload)
        credentials = saml.assume_role(args.duration)['Credentials']

        ch = CredentialsHelper(credentials)

        if args.export:
            print(ch.configure_export())
        elif args.console:
            session_duration = args.duration or saml.duration
            signin_url = ch.console_signin(session_duration)
            print(signin_url)
            if args.browser:
                webbrowser.open_new_tab(signin_url)
        else:
            ch.configure_cli(aws_profile)
    except (AssumeRoleValidationError, BotoClientError) as e:
        sys.exit(f'{e} (request id: {e.request_id})')
    except KeyboardInterrupt:
        sys.exit(1)


class DurationAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 900:
            parser.error(f'argument {option_string}: minimum value is 900')
        setattr(namespace, self.dest, values)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--region', default=os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1'))
    parser.add_argument('--no-headless', dest='headless', action='store_false', default=True, help='show web browser')
    parser.add_argument('--no-spinner', dest='spinner', action='store_false', default=True, help='disable all spinners')
    subparsers = parser.add_subparsers()

    configure_parser = subparsers.add_parser('configure')
    configure_parser.add_argument('--url')
    configure_parser.add_argument('--username')
    configure_parser.add_argument('--app-id')
    configure_parser.add_argument('-p', '--profile', default='default', help='AWS SSO Profile (default: default)')
    configure_parser.add_argument('--aws-profile', help='AWS CLI Profile (default: same as --profile)')
    configure_parser.add_argument('-f', '--force-refresh', action='store_true', default=False)
    configure_parser.set_defaults(func=configure)

    login_parser = subparsers.add_parser('login')
    login_parser.add_argument('-p', '--profile', default='default', help='AWS SSO Profile (default: default)')
    login_parser.add_argument('--aws-profile', help='override configured AWS CLI Profile')
    login_parser.add_argument('-d', '--duration', action=DurationAction, type=int, help='duration (seconds) of the role session (default/maximum: from SAML payload, minimum: 900)')
    login_parser_group = login_parser.add_mutually_exclusive_group()
    login_parser_group.add_argument('-e', '--export', action='store_true', default=False, help='outputs credentials as environment variables')
    login_parser_group.add_argument('-c', '--console', action='store_true', default=False, help='outputs AWS Console Sign In url')
    login_parser.add_argument('--browser', action='store_true', default=False, help='opens web browser with AWS Console Sign In url')
    login_parser.add_argument('-i', '--interactive', action='store_true', default=False, help='lets you interactively choose AWS account and role')
    login_parser.add_argument('-f', '--force-refresh', action='store_true', default=False)
    login_parser.set_defaults(func=login)

    args = parser.parse_args()

    try:
        func = args.func
        if callable(func):
            func(args)
    except AttributeError:
        parser.print_help(sys.stderr)
