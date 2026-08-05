#  Copyright (c) ZenML GmbH 2026. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

from typing import Any, List, Tuple, Type

import pytest
from sqlalchemy.dialects import sqlite
from sqlmodel import select

from zenml.zen_stores.schemas.code_repository_schemas import (
    CodeRepositorySchema,
)
from zenml.zen_stores.schemas.deployment_schemas import DeploymentSchema
from zenml.zen_stores.schemas.flavor_schemas import FlavorSchema
from zenml.zen_stores.schemas.hook_invocation_schemas import (
    HookInvocationSchema,
)
from zenml.zen_stores.schemas.pipeline_build_schemas import PipelineBuildSchema
from zenml.zen_stores.schemas.pipeline_run_schemas import PipelineRunSchema
from zenml.zen_stores.schemas.step_run_schemas import StepRunSchema

# Columns that are only read into a response's metadata, so an unhydrated query
# has no reason to fetch them. Deferring a column that is read unconditionally
# would replace one query with one lazy load per row, so every entry here was
# checked against its schema's `to_model`.
DEFERRED_COLUMNS: List[Tuple[Type[Any], str]] = [
    (StepRunSchema, "source_code"),
    (StepRunSchema, "docstring"),
    (StepRunSchema, "exception_info"),
    (PipelineRunSchema, "orchestrator_environment"),
    (PipelineRunSchema, "exception_info"),
    (PipelineBuildSchema, "images"),
    (FlavorSchema, "config_schema"),
    (DeploymentSchema, "deployment_metadata"),
    (DeploymentSchema, "auth_key"),
    (HookInvocationSchema, "exception_info"),
    (CodeRepositorySchema, "config"),
]

IDS = [
    f"{schema.__tablename__}.{column}" for schema, column in DEFERRED_COLUMNS
]


def _compiled_query(schema: Type[Any], include_metadata: bool) -> str:
    query = select(schema).options(
        *schema.get_query_options(include_metadata=include_metadata)
    )
    return str(query.compile(dialect=sqlite.dialect()))


@pytest.mark.parametrize("schema,column", DEFERRED_COLUMNS, ids=IDS)
def test_large_columns_are_not_fetched_without_metadata(
    schema: Type[Any], column: str
) -> None:
    """Tests that unhydrated queries skip the metadata-only columns."""
    assert f"{schema.__tablename__}.{column}" not in _compiled_query(
        schema, include_metadata=False
    )


@pytest.mark.parametrize("schema,column", DEFERRED_COLUMNS, ids=IDS)
def test_large_columns_are_fetched_with_metadata(
    schema: Type[Any], column: str
) -> None:
    """Tests that hydrated queries still fetch the metadata-only columns."""
    assert f"{schema.__tablename__}.{column}" in _compiled_query(
        schema, include_metadata=True
    )
