#!/usr/bin/env python3
from aws_cdk import (
    core as core_
)
from cdk_helper import (
    CiCdConfig,
    VERSION as CDKHelper_VERSION,
    Tags,
)
# noinspection PyUnresolvedReferences
from aws_lambda import __version__ as PythonLambda_VERSION
# noinspection PyUnresolvedReferences
from lambdacore.utils import want_version
# noinspection PyUnresolvedReferences
from lambdacore.logs import LOGGER

from cicd_cdk.cicd_lib.cicd_stack import CicdStack

cicd_config = CiCdConfig.singleton()
cicd_tags = Tags.singleton(extra_tags=cicd_config.config.get('tags', {}))
product_tag = cicd_tags.map["Product"]
env = core_.Environment(account=str(cicd_config.account.id), region=cicd_config.account.get('region', cicd_config.defaults.region))

want_version(package='cdk_helper', actual=CDKHelper_VERSION, target=cicd_config.config.get('packages', {}).get('cdk_helper', {}).get('version', '0.4.9'))
want_version(package='python_lambda', actual=PythonLambda_VERSION, target=cicd_config.config.get('packages', {}).get('python_lambda', {}).get('version', '11.7.1rev15'))


def stack(app, name='BlockList-API', cicd_config=None, cicd_tags=None):
    CicdStack(app, f'{product_tag}-cicd-cdk', cicd_config=cicd_config, cicd_tags=cicd_tags)



def main():
    app = core_.App()
    stack(app, cicd_config=cicd_config, cicd_tags=cicd_tags)
    app.synth()

if __name__ == '__main__':
    main()
