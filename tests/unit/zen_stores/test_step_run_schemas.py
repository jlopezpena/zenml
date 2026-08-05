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

import pytest
from sqlalchemy.dialects import sqlite
from sqlmodel import select

from zenml.zen_stores.schemas.step_run_schemas import StepRunSchema

# Only read into `StepRunResponseMetadata`, and together they are the bulk of a
# step run row.
METADATA_ONLY_COLUMNS = ["source_code", "docstring", "exception_info"]


def _compiled_query(include_metadata: bool) -> str:
    query = select(StepRunSchema).options(
        *StepRunSchema.get_query_options(include_metadata=include_metadata)
    )
    return str(query.compile(dialect=sqlite.dialect()))


@pytest.mark.parametrize("column_name", METADATA_ONLY_COLUMNS)
def test_large_columns_are_not_fetched_without_metadata(
    column_name: str,
) -> None:
    """Tests that unhydrated step run queries skip the large columns."""
    assert f"step_run.{column_name}" not in _compiled_query(
        include_metadata=False
    )


@pytest.mark.parametrize("column_name", METADATA_ONLY_COLUMNS)
def test_large_columns_are_fetched_with_metadata(column_name: str) -> None:
    """Tests that hydrated step run queries still fetch the large columns."""
    assert f"step_run.{column_name}" in _compiled_query(include_metadata=True)
