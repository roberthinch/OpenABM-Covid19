import itertools
from dataclasses import dataclass, field
from typing import Mapping, Tuple, Any

import numpy as np

from adapter_covid19.constants import START_OF_TIME
from adapter_covid19.datasources import (
    SectorDataSource,
    Reader,
    RegionSectorAgeDataSource,
)
from adapter_covid19.enums import Sector, LabourState, Region, Age


@dataclass
class InitialiseState:
    economics_kwargs: Mapping[str, Any] = field(default_factory=dict)
    gdp_kwargs: Mapping[str, Any] = field(default_factory=dict)
    personal_kwargs: Mapping[str, Any] = field(default_factory=dict)
    corporate_kwargs: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class SimulateState:
    time: int
    lockdown: bool  # TODO: remove
    utilisations: Mapping[Tuple[LabourState, Region, Sector, Age], float]
    economics_kwargs: Mapping[str, Any] = field(default_factory=dict)
    gdp_kwargs: Mapping[str, Any] = field(default_factory=dict)
    personal_kwargs: Mapping[str, Any] = field(default_factory=dict)
    corporate_kwargs: Mapping[str, Any] = field(default_factory=dict)


class Scenario:
    gdp: Mapping[Tuple[Region, Sector, Age], float]
    workers: Mapping[Tuple[Region, Sector, Age], float]
    furloughed: Mapping[Sector, float]
    keyworker: Mapping[Sector, float]

    def __init__(self,
                 lockdown_recovery_time: float = 1,
                 furlough_start_time = None,
                 furlough_end_time = None):
        self.datasources = {
            "gdp": RegionSectorAgeDataSource,
            "workers": RegionSectorAgeDataSource,
            "furloughed": SectorDataSource,
            "keyworker": SectorDataSource,
        }
        self.lockdown_recovery_time = lockdown_recovery_time
        self.lockdown_exited_time = 0
        self.furlough_start_time = furlough_start_time
        self.furlough_end_time = furlough_end_time
        self._has_been_lockdown = False
        self._utilisations = {}  # For tracking / debugging
        for k in self.datasources:
            self.__setattr__(k, None)

    def load(self, reader: Reader) -> None:
        for k, v in self.datasources.items():
            self.__setattr__(k, v(k).load(reader))

    def _apply_lockdown(
        self,
        time: int,
        lockdown: bool,
        healthy: Mapping[Tuple[Region, Sector, Age], float],
        ill: Mapping[Tuple[Region, Sector, Age], float],
    ) -> Mapping[Tuple[LabourState, Region, Sector, Age], float]:
        """
        Convert healthy/ill utilisations to working, ill, furloughed, wfh utilisations

        :param time:
        :param lockdown:
        :param healthy:
        :param ill:
        :return:
        """
        furlough_active = self.furlough_start_time is not None and self.furlough_end_time is not None \
                        and self.furlough_start_time <= time < self.furlough_end_time
        furloughed = self.furloughed  if furlough_active else {s: 0.0 for s in Sector}

        utilisations = {
            k: 0 for k in itertools.product(LabourState, Region, Sector, Age)
        }
        if not lockdown and not self.lockdown_exited_time:
            # i.e. we're not in lockdown and we've not exited lockdown
            for r, s, a in itertools.product(Region, Sector, Age):
                utilisations[LabourState.WORKING, r, s, a] = healthy[r, s, a]
                utilisations[LabourState.ILL, r, s, a] = ill[r, s, a]
            return utilisations
        # We assume all utilisations are given as WFH=0, and here we adjust for WFH
        base_utilisations = {
            (r, s, a): u * self.keyworker[s] for (r, s, a), u in healthy.items()
        }
        # Lockdown utilisations
        work_utilisations = {
            (r, s, a): base_utilisations[r, s, a] * (1 - furloughed[s])
            for r, s, a in itertools.product(Region, Sector, Age)
        }
        wfh_utilisations = {
            (r, s, a): (healthy[r, s, a] - base_utilisations[r, s, a])
            * (1 - furloughed[s])
            for r, s, a in itertools.product(Region, Sector, Age)
        }
        furlough_utilisations = {
            (r, s, a): healthy[r, s, a] * furloughed[s]
            for r, s, a in itertools.product(Region, Sector, Age)
        }
        if self.lockdown_exited_time:
            # Slowly bring people back to work and out of furlough
            # TODO: this assumes noone transitions from furloughed to unemployed
            factor = min(
                (time - self.lockdown_exited_time) / self.lockdown_recovery_time, 1
            )
            furlough_utilisations = {
                k: (1 - factor) * v for k, v in furlough_utilisations.items()
            }
            work_utilisations = {
                k: (base_utilisations[k] + factor * (healthy[k] - base_utilisations[k]))
                * (1 - furlough_utilisations[k])
                for k in itertools.product(Region, Sector, Age)
            }
            wfh_utilisations = {
                k: (healthy[k] - base_utilisations[k])
                * (1 - factor)
                * (1 - furlough_utilisations[k])
                for k in itertools.product(Region, Sector, Age)
            }

        for r, s, a in itertools.product(Region, Sector, Age):
            utilisations[LabourState.WORKING, r, s, a] = work_utilisations[r, s, a]
            utilisations[LabourState.WFH, r, s, a] = wfh_utilisations[r, s, a]
            utilisations[LabourState.FURLOUGHED, r, s, a] = furlough_utilisations[
                r, s, a
            ]
            utilisations[LabourState.ILL, r, s, a] = ill[r, s, a]
            assert np.isclose(sum(utilisations[l, r, s, a] for l in LabourState), 1)
        return utilisations

    def _pre_simulation_checks(self, time: int, lockdown: bool) -> None:
        if time == START_OF_TIME and lockdown:
            raise ValueError(
                "Economics model requires simulation to be started before lockdown"
            )
        if self.lockdown_exited_time and lockdown:
            raise NotImplementedError(
                "Bankruptcy/insolvency logic for toggling lockdown needs doing"
            )
        if lockdown and not self._has_been_lockdown:
            self._has_been_lockdown = True
        if not self.lockdown_exited_time and self._has_been_lockdown and not lockdown:
            self.lockdown_exited_time = time

    def initialise(self) -> InitialiseState:
        return InitialiseState()

    def generate(
        self,
        time: int,
        lockdown: bool,
        healthy: Mapping[Tuple[Region, Sector, Age], float],
        ill: Mapping[Tuple[Region, Sector, Age], float],
    ) -> SimulateState:
        self._pre_simulation_checks(time, lockdown)
        utilisations = self._apply_lockdown(time, lockdown, healthy, ill)
        self._utilisations[time] = utilisations  # For tracking / debugging
        return SimulateState(time, lockdown, utilisations)