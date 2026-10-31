#!/usr/bin/env python3
"""Query a Lambda heat pump controller and print every value.

Connects to a controller, reads it once, and dumps every sub-system's values to
the terminal — handy for checking a real device without Home Assistant in the
way. It talks to the same lambda_modbus library the integration uses, so what it
prints is what the integration would see.

    python script/query.py 192.168.1.50 --num-hps 2 --num-boil 1

The controller only tells you how many modules it has by answering (or not), so
pass the counts you configured in the integration.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

from modbus_connection import ModbusError
from modbus_connection.cli_helper import (
    CountingUnit,
    add_connection_args,
    connect_from_args,
    print_component,
)

# Import the device library on its own, without the integration package around
# it — it has no Home Assistant dependency, and this is how it would be imported
# once it is split out into its own PyPI package.
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "lambda_heat_pumps"))

from lambda_modbus import LambdaHeatPump  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # The controller speaks native Modbus TCP, so that is all the CLI offers.
    add_connection_args(parser, connections=(("tcp", "socket"),))

    parser.add_argument("--unit", type=int, default=1, help="Modbus unit id (default: 1)")
    parser.add_argument("--num-hps", type=int, default=1, help="heat pumps (default: 1)")
    parser.add_argument("--num-boil", type=int, default=1, help="boilers (default: 1)")
    parser.add_argument("--num-buff", type=int, default=0, help="buffers (default: 0)")
    parser.add_argument("--num-sol", type=int, default=0, help="solar modules (default: 0)")
    parser.add_argument("--num-hc", type=int, default=1, help="heating circuits (default: 1)")
    parser.add_argument(
        "--word-order",
        choices=("big", "little"),
        default="big",
        help="word order of the 32-bit counters (default: big, i.e. high word first)",
    )
    return parser.parse_args()


def _print(controller: LambdaHeatPump) -> None:
    print_component(controller.ambient, title="Ambient")
    print_component(controller.e_manager, title="E-Manager")
    for index, heat_pump in enumerate(controller.heat_pumps, 1):
        print_component(heat_pump, title=f"Heat pump {index}")
    for index, boiler in enumerate(controller.boilers, 1):
        print_component(boiler, title=f"Boiler {index}")
    for index, buffer in enumerate(controller.buffers, 1):
        print_component(buffer, title=f"Buffer {index}")
    for index, solar in enumerate(controller.solar_modules, 1):
        print_component(solar, title=f"Solar {index}")
    for index, circuit in enumerate(controller.heating_circuits, 1):
        print_component(circuit, title=f"Heating circuit {index}")


async def _run(args: argparse.Namespace) -> int:
    try:
        connection = await connect_from_args(args)
    except ModbusError as err:
        print(f"Could not connect: {err}", file=sys.stderr)
        return 1

    counting = CountingUnit(connection.for_unit(args.unit))
    try:
        controller = LambdaHeatPump(
            counting,
            num_hps=args.num_hps,
            num_boil=args.num_boil,
            num_buff=args.num_buff,
            num_sol=args.num_sol,
            num_hc=args.num_hc,
            word_order=args.word_order,
        )
        start = time.monotonic()
        await controller.async_update()
        elapsed = time.monotonic() - start
    except ModbusError as err:
        print(f"Error reading device: {err}", file=sys.stderr)
        return 1
    finally:
        await connection.close()

    _print(controller)
    print(f"\nQueried in {elapsed * 1000:.0f} ms ({counting.reads} Modbus reads)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run(_parse_args())))
