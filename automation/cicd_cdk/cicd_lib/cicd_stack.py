from aws_cdk import (
    core as core_,
    aws_codebuild as cb_,
    aws_codepipeline as cp_,
    aws_iam as iam_,
    aws_events as evt_,
)

# noinspection PyUnresolvedReferences
from cdk_helper import (
    CiCdConfig,
    Tags
)
import typing


class CicdStack(core_.Stack):

    def __init__(self, scope: core_.Construct, id: str,
                 cicd_config: typing.Optional["CiCdConfig"] = None,
                 cicd_tags: typing.Optional["Tags"] = None,
                 **kwargs) -> None:

        self.cicd_config = cicd_config if cicd_config else CiCdConfig.singleton()
        self.cicd_tags = cicd_tags if cicd_tags else Tags.singleton(extra_tags=self.cicd_config.config.get('tags', {}))
        tags = self.cicd_tags.map
        tags['Name'] = id
        self.version_tag = self.cicd_tags.map['Version']
        if not kwargs.get('tags', None):
            kwargs['tags'] = tags
        if not kwargs.get('description', None):
            kwargs['description'] = f'{id} - v{self.version_tag}'

        super().__init__(scope, id, **kwargs)

        self.__construct__(cicd_config=cicd_config, **kwargs)

    def __construct__(self,
                      cicd_config: typing.Optional["CiCdConfig"] = None,
                      cicd_tags: typing.Optional["Tags"] = None,
                      **kwargs) -> None:
        # Parameters
        core_.CfnParameter(self, 'CiCdArtifactStoreBucketArn', type='String')
        core_.CfnParameter(self, 'CiCdArtifactStoreBucketName', type='String')
        self.codeartifact_domain_name = 'artifacts'

        self.product_tag = self.cicd_tags.map["Product"]
        self.codebuild_project_name = f'{self.product_tag}-codebuild-project'

        self.source_repository_name = self.product_tag
        self.source_repository_branch = self.cicd_tags.map.get('Branch', 'develop')

        self._iam_construct()
        self._codebuild_construct()
        self._codepipeline_construct()

    def _iam_construct(self):
        # principal = iam_.AccountPrincipal(self.cicd_config.accounts[self.cicd_config.defaults.cicdAccount].id)

        principals = [
            iam_.ServicePrincipal(service='codepipeline.amazonaws.com'),
            iam_.ServicePrincipal(service='codedeploy.amazonaws.com'),
            iam_.ServicePrincipal(service='codebuild.amazonaws.com'),
        ]

        self.service_role_name = f'{self.product_tag}-CICD-ServiceRole'
        stmts = {}
        stmts['sts-get'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'sts:GetSessionToken',
                'sts:GetAccessKeyInfo',
                'sts:GetCallerIdentity',
                'sts:GetServiceBearerToken',
            ],
            resources=['*']
        )
        stmts['sts-fed'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'sts:GetFederationToken',
            ],
            resources=[core_.Fn.sub(body='arn:aws:sts::${AWS::AccountId}:assumed-role/' + self.service_role_name + '/*')]
        )
        stmts['codeartifact-list'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'codeartifact:ListRepositories',
                'codeartifact:ListDomains',
            ],
            resources=['*']
        )
        stmts['codeartifact-rest'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'codeartifact:GetPackageVersionReadme',
                'codeartifact:DeletePackageVersions',
                'codeartifact:ListRepositoriesInDomain',
                'codeartifact:DescribePackageVersion',
                'codeartifact:GetDomainPermissionsPolicy',
                'codeartifact:DisposePackageVersions',
                'codeartifact:ListPackageVersionDependencies',
                'codeartifact:ListPackages',
                'codeartifact:GetAuthorizationToken',
                'codeartifact:ReadFromRepository',
                'codeartifact:GetPackageVersionAsset',
                'codeartifact:DescribeRepository',
                'codeartifact:ListPackageVersionAssets',
                'codeartifact:DescribeDomain',
                'codeartifact:CopyPackageVersions',
                'codeartifact:PutPackageMetadata',
                'codeartifact:UpdatePackageVersionsStatus',
                'codeartifact:GetRepositoryEndpoint',
                'codeartifact:PublishPackageVersion',
                'codeartifact:GetRepositoryPermissionsPolicy',
                'codeartifact:ListPackageVersions',
            ],
            resources=[
                core_.Fn.sub(
                    body='arn:aws:codeartifact:${AWS::Region}:${AWS::AccountId}:package/' + self.codeartifact_domain_name + '/*/*/*/*'),
                core_.Fn.sub(
                    body='arn:aws:codeartifact:${AWS::Region}:${AWS::AccountId}:domain/' + self.codeartifact_domain_name + ''),
                core_.Fn.sub(
                    body='arn:aws:codeartifact:${AWS::Region}:${AWS::AccountId}:repository/' + self.codeartifact_domain_name + '/*'),
            ]
        )
        stmts['codecommit'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'codecommit:Batch*',
                'codecommit:Cancel*',
                'codecommit:Describe*',
                'codecommit:Get*',
                'codecommit:Git*',
                'codecommit:Upload*',
            ],
            resources=[
                core_.Fn.sub(body='arn:aws:codecommit:${AWS::Region}:${AWS::AccountId}:' + self.product_tag + ''),
            ]
        )
        stmts['logs'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents',
            ],
            resources=[
                core_.Fn.sub(
                    body='arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:codebuild:log-stream:' + self.codebuild_project_name + ''),
                core_.Fn.sub(
                    body='arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:codebuild:log-stream:' + self.codebuild_project_name + '/*'),
            ]
        )
        stmts['s3'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                's3:*',
            ],
            resources=[
                core_.Fn.sub(body='${CiCdArtifactStoreBucketArn}'),
                core_.Fn.sub(body='${CiCdArtifactStoreBucketArn}/*'),
            ]
        )
        stmts['iam'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'iam:PassRole',
            ],
            resources=['*'],
            conditions={
                'StringEqualsIfExists': {
                    'iam:PassedToService': [
                        'cloudformation.amazonaws.com',
                        'elasticbeanstalk.amazonaws.com',
                        'ec2.amazonaws.com',
                        'ecs-tasks.amazonaws.com',
                    ]}}
        )
        stmts['codebuild'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'codebuild:*',
            ],
            resources=[
                core_.Fn.sub(body='arn:aws:codecommit:${AWS::Region}:${AWS::AccountId}:' + self.product_tag + ''),
            ]
        )

        pol = iam_.PolicyDocument(statements=list(stmts.values()))
        tags = self.cicd_tags.cfntag_list
        tags.append(core_.CfnTag(key='Name', value=self.service_role_name))
        self.service_role = iam_.CfnRole(self, 'CICDServiceRole',
                                         assume_role_policy_document=iam_.PolicyDocument(
                                             statements=[iam_.PolicyStatement(
                                                 actions=['sts:AssumeRole'],
                                                 effect=iam_.Effect.ALLOW,
                                                 principals=principals)],
                                         ),
                                         managed_policy_arns=[
                                             'arn:aws:iam::aws:policy/AWSCodeDeployDeployerAccess',
                                             'arn:aws:iam::aws:policy/AWSCodeCommitReadOnly',
                                             'arn:aws:iam::aws:policy/AWSCodeBuildReadOnlyAccess',
                                             'arn:aws:iam::aws:policy/AWSCodeArtifactReadOnlyAccess',
                                             'arn:aws:iam::aws:policy/AWSCodeDeployReadOnlyAccess',
                                             'arn:aws:iam::aws:policy/AWSCodePipelineReadOnlyAccess',
                                         ],
                                         policies=[iam_.CfnRole.PolicyProperty(policy_name=f'{stnm}-policy',
                                                                               policy_document=iam_.PolicyDocument(
                                                                                   statements=[stmt])) for stnm, stmt in
                                                   stmts.items()],
                                         role_name=self.service_role_name,
                                         tags=tags,
                                         )


    def _codebuild_construct(self):
        tags = self.cicd_tags.cfntag_list
        name = self.codebuild_project_name
        tags.append(core_.CfnTag(key='Name', value=f'{self.product_tag}-codebuild-project'))
        cbp = cb_.CfnProject(self, 'CodeBuildProject',
                             artifacts=cb_.CfnProject.ArtifactsProperty(type='CODEPIPELINE'),
                             badge_enabled=False,
                             cache=cb_.CfnProject.ProjectCacheProperty(type='NO_CACHE'),
                             description=name,
                             environment=cb_.CfnProject.EnvironmentProperty(compute_type='BUILD_GENERAL1_SMALL',
                                                                            image='aws/codebuild/standard:4.0',
                                                                            image_pull_credentials_type='CODEBUILD',
                                                                            privileged_mode=True,
                                                                            type='LINUX_CONTAINER'),
                             logs_config=cb_.CfnProject.LogsConfigProperty(
                                 cloud_watch_logs=cb_.CfnProject.CloudWatchLogsConfigProperty(status='ENABLED',
                                                                                              group_name='codebuild',
                                                                                              stream_name=name
                                                                                              )),
                             name=name,  # CodeBuildProject
                             service_role=self.service_role.attr_arn,
                             source=cb_.CfnProject.SourceProperty(type='CODEPIPELINE',
                                                                  build_spec='buildspec.yaml',
                                                                  # location=core_.Fn.ref('CodeBuildSourceLocation'),
                                                                  # source_identifier=f'{self.product_tag}-codepipeline-source'
                                                                  ),
                             timeout_in_minutes=60,
                             tags=tags,
                             )
        stmts = {}
        stmts['codebuild'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'codebuild:*',
            ],
            resources=[
                cbp.attr_arn,
                core_.Fn.sub(
                    body='arn:aws:codebuild:${AWS::Region}:${AWS::AccountId}:report-group/' + self.product_tag + '-*'),
            ]
        )
        iam_.CfnPolicy(self, 'CodebuildPolicy',
                       policy_document=iam_.PolicyDocument(statements=list(stmts.values())),
                       policy_name=f'{self.product_tag}-codebuild-policy',
                       roles=[self.service_role_name],
                       )
        self.codebuild_project = cbp


    def _codepipeline_construct(self):
        tags = self.cicd_tags.cfntag_list
        name = f'{self.codebuild_project_name}-codepipeline'
        tags.append(core_.CfnTag(key='Name', value=f'{self.product_tag}-codepipeline'))

        self.codepipeline = cp_.CfnPipeline(self, 'CodePipeline',
                                            artifact_store=cp_.CfnPipeline.ArtifactStoreProperty(
                                                location=core_.Fn.ref(logical_name='CiCdArtifactStoreBucketName'),
                                                type='S3'
                                            ),
                                            name=name,
                                            role_arn=self.service_role.attr_arn,
                                            stages=[
                                                cp_.CfnPipeline.StageDeclarationProperty(
                                                    name='Source',
                                                    actions=[
                                                        cp_.CfnPipeline.ActionDeclarationProperty(name='SourceAction',
                                                                                                  action_type_id=cp_.CfnPipeline.ActionTypeIdProperty(
                                                                                                      category='Source',
                                                                                                      owner='AWS',
                                                                                                      version='1',
                                                                                                      provider='CodeCommit'
                                                                                                  ),
                                                                                                  output_artifacts=[
                                                                                                      cp_.CfnPipeline.OutputArtifactProperty(
                                                                                                          name='SourceOutput'),
                                                                                                  ],
                                                                                                  configuration={
                                                                                                      'RepositoryName': self.source_repository_name,
                                                                                                      'BranchName': self.source_repository_branch,
                                                                                                      'PollForSourceChanges': False,
                                                                                                  },
                                                                                                  run_order=1
                                                                                                  ),
                                                    ],
                                                ),
                                                cp_.CfnPipeline.StageDeclarationProperty(
                                                    name='Build',
                                                    actions=[
                                                        cp_.CfnPipeline.ActionDeclarationProperty(name='BuildAction',
                                                                                                  input_artifacts=[
                                                                                                      cp_.CfnPipeline.InputArtifactProperty(
                                                                                                          name='SourceOutput'
                                                                                                      ),
                                                                                                  ],
                                                                                                  action_type_id=cp_.CfnPipeline.ActionTypeIdProperty(
                                                                                                      category='Build',
                                                                                                      owner='AWS',
                                                                                                      version='1',
                                                                                                      provider='CodeBuild'
                                                                                                  ),
                                                                                                  configuration={
                                                                                                      'ProjectName': self.codebuild_project_name,
                                                                                                      'PrimarySource': 'SourceOutput',
                                                                                                  },
                                                                                                  run_order=1
                                                                                                  ),
                                                    ],
                                                ),
                                            ],
                                            tags=tags
                                            )

        stmts = {}
        stmts['codepipeline'] = iam_.PolicyStatement(
            effect=iam_.Effect.ALLOW,
            actions=[
                'codepipeline:StartPipelineExecution',
            ],
            resources=[
                core_.Fn.sub(body='arn:aws:codepipeline:${AWS::Region}:${AWS::AccountId}:${CodePipeline}'),
            ]
        )

        pol = iam_.PolicyDocument(statements=list(stmts.values()))

        trigger = f'{self.product_tag}-codepipeline-trigger'

        trigger_role = iam_.CfnRole(self, 'PipelineTriggerRole',
                                    assume_role_policy_document=iam_.PolicyDocument(
                                        statements=[iam_.PolicyStatement(
                                            actions=['sts:AssumeRole'],
                                            effect=iam_.Effect.ALLOW,
                                            principals=[iam_.ServicePrincipal(service='events.amazonaws.com')])],
                                    ),
                                    managed_policy_arns=[
                                        'arn:aws:iam::aws:policy/AWSCodeDeployDeployerAccess',
                                        'arn:aws:iam::aws:policy/AWSCodeCommitReadOnly',
                                        'arn:aws:iam::aws:policy/AWSCodeBuildReadOnlyAccess',
                                        'arn:aws:iam::aws:policy/AWSCodeArtifactReadOnlyAccess',
                                        'arn:aws:iam::aws:policy/AWSCodeDeployReadOnlyAccess',
                                        'arn:aws:iam::aws:policy/AWSCodePipelineReadOnlyAccess',
                                    ],
                                    path='/service-role/',
                                    policies=[iam_.CfnRole.PolicyProperty(policy_name=f'{stnm}-policy',
                                                                          policy_document=iam_.PolicyDocument(
                                                                              statements=[stmt])) for stnm, stmt in
                                              stmts.items()],
                                    role_name=f'{self.product_tag}-codepipeline-trigger-role',
                                    tags=tags,
                                    )

        trigger_rule = evt_.CfnRule(self, 'PipelineTriggerRule',
                                    description=trigger,
                                    name=trigger,
                                    state='ENABLED',
                                    event_pattern={
                                        'source': ['aws.codecommit'],
                                        "detail-type": [
                                            "CodeCommit Repository State Change"
                                        ],
                                        "resources": [
                                            core_.Fn.sub(
                                                body="arn:aws:codecommit:${AWS::Region}:${AWS::AccountId}:" + self.source_repository_name),
                                        ],
                                        "detail": {
                                            "event": [
                                                "referenceCreated",
                                                "referenceUpdated"
                                            ],
                                            "referenceType": [
                                                "branch"
                                            ],
                                            "referenceName": [
                                                self.source_repository_branch
                                            ]
                                        }
                                    },
                                    targets=[
                                        evt_.CfnRule.TargetProperty(arn=core_.Fn.sub(
                                            body='arn:aws:codepipeline:${AWS::Region}:${AWS::AccountId}:${CodePipeline}'),
                                                                    id=core_.Fn.ref('CodePipeline'),
                                                                    role_arn=trigger_role.attr_arn
                                                                    )
                                    ],
                                    )
