from functools import partial
from typing import Collection

from pandas import DataFrame, concat

from structure_scripts.aisc.connections.compositions import (
    ConnectionRuleCheckAndStrengths, ConnectionRuleCheck,
)
from structure_scripts.aisc.criteria import DesignType


def _check_connection(
    results: DataFrame,
    connection: ConnectionRuleCheck,
    case_names: Collection[str],
    design_criteria: DesignType = DesignType.ASD,
):
    new_df = DataFrame()
    for name in case_names:
        func = partial(
            connection.check_result,
            case_name=name,
            design_criteria=design_criteria,
        )
        new_df = concat((new_df, results.apply(func, axis=1)), axis=1)
    return new_df


def _check_connections(
    results: DataFrame,
    connections: Collection[ConnectionRuleCheck] | ConnectionRuleCheck,
    case_names: Collection[str],
    design_criteria: DesignType = DesignType.ASD,
):
    df = DataFrame()
    if isinstance(connections, ConnectionRuleCheck):
        connections = connections,
    for connection in connections:
        df = concat(
            (
                df,
                _check_connection(
                    results=results,
                    connection=connection,
                    case_names=case_names,
                    design_criteria=design_criteria
                )
            ),
            axis=1
        )
    return df


def check_connections(
    results: dict[str, DataFrame],
    connections: dict[str, Collection[ConnectionRuleCheck] | ConnectionRuleCheck],
    case_names: Collection[str],
    design_criteria: DesignType = DesignType.ASD,
):
    if not all(
        item in list(results.keys()) for item in list(connections.keys())
    ):
        raise ValueError("All keys in results must also exit in connections")
    return {
        key: _check_connections(
            results=value,
            connections=connections[key],
            case_names=case_names,
            design_criteria=design_criteria,
        )
        for key, value in results.items()
    }


# def compose_connection()
