#!/usr/bin/env python3

from aws_cdk import core
from cdk_helper import (
    Tags,
    CiCdConfig
)
from cicd_cdk.cicd_lib.cicd_stack import CicdStack

cicd_config = CiCdConfig.singleton()
cicd_tags = Tags.singleton(extra_tags=cicd_config.config.get('tags', {}))
product_tag = cicd_tags.map["Product"]

app = core.App()
CicdStack(app, f'{product_tag}-cicd-cdk', cicd_config=cicd_config, cicd_tags=cicd_tags)

app.synth()
