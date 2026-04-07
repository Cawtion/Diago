"""
TSB Manager - Technical Service Bulletin Integration
Provides search, matching, and integration with Diago's diagnostic engine.
"""
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class TSBEntry:
    tsb_id: str
    title: str
    description: str
    make: str
    model: str
    year_start: int
    year_end: int
    engine_codes: List[str]
    related_dtcs: List[str]
    systems: List[str]
    symptoms: List[str]
    root_cause: str
    repair_procedure: str
    parts_required: List[str]
    labor_hours: float
    source_url: str
    published_date: str
    last_updated: str
    relevance_score: float = 0.0


@dataclass
class TSBMatch:
    tsb: TSBEntry
    match_score: float
    matched_codes: List[str]
    matched_symptoms: List[str]
    reason: str


class TSBManager:
    SAMPLE_TSBS = [
        TSBEntry(
            tsb_id="TSB-2020-001", title="Transmission Shudder During Light Acceleration",
            description="Some vehicles may exhibit a shudder or vibration during light acceleration, typically between 30-50 mph.",
            make="Ford", model="F-150", year_start=2017, year_end=2020,
            engine_codes=["3.5L EcoBoost", "2.7L EcoBoost"],
            related_dtcs=["P0741", "P0742", "P0776"], systems=["transmission"],
            symptoms=["shudder", "vibration", "jerking", "rough shifting"],
            root_cause="Torque converter clutch wear causing slip",
            repair_procedure="1. Verify TSB\n2. Test drive\n3. Replace torque converter\n4. Flush fluid\n5. Reprogram TCM",
            parts_required=["Torque converter", "Transmission fluid", "Gasket set"],
            labor_hours=8.5, source_url="https://www.fordtechservice.dealer.com",
            published_date="2020-03-15", last_updated="2020-03-15",
        ),
        TSBEntry(
            tsb_id="TSB-2019-002", title="Excessive Oil Consumption",
            description="Some vehicles may exhibit excessive oil consumption requiring frequent top-offs.",
            make="Subaru", model="Outback", year_start=2013, year_end=2017,
            engine_codes=["2.5L FB25"], related_dtcs=["P0171", "P0420"],
            systems=["engine"], symptoms=["oil consumption", "low oil", "blue smoke"],
            root_cause="Piston ring design allows oil to enter combustion chamber",
            repair_procedure="1. Oil consumption test\n2. If >1qt/1000mi replace short block\n3. Update PCM",
            parts_required=["Short block assembly", "Gasket set", "Oil"],
            labor_hours=18.0, source_url="https://www.subaru.com/TSB",
            published_date="2019-06-20", last_updated="2019-06-20",
        ),
        TSBEntry(
            tsb_id="TSB-2021-003", title="Timing Chain Rattle at Startup",
            description="Some vehicles may exhibit a rattle noise for 1-2 seconds at cold startup.",
            make="BMW", model="3 Series", year_start=2012, year_end=2018,
            engine_codes=["N20", "N26"], related_dtcs=["P0011", "P0012", "P0016"],
            systems=["engine"], symptoms=["rattle", "chain noise", "ticking", "startup noise"],
            root_cause="Timing chain tensioner loses pressure when engine is off",
            repair_procedure="1. Verify cold startup noise\n2. Replace tensioner\n3. Inspect chain\n4. Replace if stretched",
            parts_required=["Timing chain tensioner", "Timing chain", "Gaskets"],
            labor_hours=12.0, source_url="https://www.bmw-tsb.com",
            published_date="2021-01-10", last_updated="2021-01-10",
        ),
        TSBEntry(
            tsb_id="TSB-2018-004", title="High Pressure Fuel Pump Failure",
            description="Some vehicles may experience extended cranking or loss of power due to HPFP failure.",
            make="BMW", model="Various", year_start=2007, year_end=2016,
            engine_codes=["N54", "N55", "S65"],
            related_dtcs=["P0087", "P0088", "P023F", "P0300"], systems=["fuel_system"],
            symptoms=["extended cranking", "rough idle", "loss of power", "fuel pressure"],
            root_cause="High pressure fuel pump internal failure",
            repair_procedure="1. Check fuel pressure\n2. Replace HPFP\n3. Update DME\n4. Clear adaptations",
            parts_required=["High pressure fuel pump", "Fuel line seals"],
            labor_hours=3.5, source_url="https://www.bmw-tsb.com",
            published_date="2018-09-05", last_updated="2018-09-05",
        ),
        TSBEntry(
            tsb_id="TSB-2022-005", title="EVAP System Small Leak",
            description="Some vehicles may set EVAP leak codes due to a faulty gas cap or minor leak.",
            make="Toyota", model="Camry", year_start=2018, year_end=2022,
            engine_codes=["2.5L", "3.5L"], related_dtcs=["P0456", "P0457", "P0442"],
            systems=["emissions"], symptoms=["check engine light", "fuel smell", "evap leak"],
            root_cause="Gas cap seal deterioration or EVAP line crack",
            repair_procedure="1. Inspect gas cap\n2. EVAP smoke test\n3. Replace components\n4. Clear codes",
            parts_required=["Gas cap", "EVAP hoses"],
            labor_hours=1.0, source_url="https://www.toyota.com/TSB",
            published_date="2022-02-28", last_updated="2022-02-28",
        ),
        TSBEntry(
            tsb_id="TSB-2017-006", title="Catalytic Converter Efficiency Below Threshold",
            description="Some vehicles may set catalyst efficiency codes due to premature failure or oil consumption.",
            make="Honda", model="Civic", year_start=2016, year_end=2019,
            engine_codes=["1.5L Turbo"], related_dtcs=["P0420", "P0430"],
            systems=["emissions"], symptoms=["check engine light", "failed emissions", "rotten egg smell"],
            root_cause="Oil contamination of catalyst from piston ring issues",
            repair_procedure="1. Check oil consumption\n2. Address oil issue\n3. Replace converter\n4. Update PCM",
            parts_required=["Catalytic converter", "Gaskets"],
            labor_hours=4.0, source_url="https://www.honda.com/TSB",
            published_date="2017-11-15", last_updated="2017-11-15",
        ),
        TSBEntry(
            tsb_id="TSB-2020-007", title="Ignition Coil Failure - Misfire",
            description="Some vehicles may experience misfire due to ignition coil failure under high load.",
            make="Volkswagen", model="Jetta", year_start=2015, year_end=2020,
            engine_codes=["1.4L TSI", "1.8L TSI"],
            related_dtcs=["P0300", "P0301", "P0302", "P0303", "P0304", "P0351", "P0352"],
            systems=["ignition"], symptoms=["misfire", "rough idle", "hesitation", "check engine light"],
            root_cause="Ignition coil internal failure due to heat",
            repair_procedure="1. Identify misfiring cylinder\n2. Swap coil\n3. Replace coil(s)\n4. Replace plugs",
            parts_required=["Ignition coil", "Spark plugs"],
            labor_hours=1.5, source_url="https://www.vw.com/TSB",
            published_date="2020-07-22", last_updated="2020-07-22",
        ),
        TSBEntry(
            tsb_id="TSB-2019-008", title="VVT Solenoid Sludge Buildup",
            description="Some vehicles may experience rough idle or poor performance due to VVT solenoid clogging.",
            make="Toyota", model="Corolla", year_start=2009, year_end=2018,
            engine_codes=["1.8L 2ZR-FE"],
            related_dtcs=["P0010", "P0011", "P0012", "P0020", "P0021"],
            systems=["engine"], symptoms=["rough idle", "stalling", "rattle", "poor performance"],
            root_cause="Oil sludge blocking VVT solenoid oil passages",
            repair_procedure="1. Remove solenoids\n2. Clean or replace\n3. Engine flush\n4. Change oil",
            parts_required=["VVT solenoid", "Engine oil", "Oil filter"],
            labor_hours=2.5, source_url="https://www.toyota.com/TSB",
            published_date="2019-04-10", last_updated="2019-04-10",
        ),
        TSBEntry(
            tsb_id="TSB-2021-009", title="Water Pump Leak - Coolant Loss",
            description="Some vehicles may experience coolant loss due to water pump seal failure.",
            make="BMW", model="X5", year_start=2014, year_end=2020,
            engine_codes=["N55", "N57"], related_dtcs=["P0115", "P0116", "P0217"],
            systems=["cooling"], symptoms=["coolant leak", "overheating", "low coolant"],
            root_cause="Water pump seal degradation",
            repair_procedure="1. Pressure test\n2. Locate leak\n3. Replace water pump\n4. Replace thermostat\n5. Flush coolant",
            parts_required=["Water pump", "Thermostat", "Coolant", "Gaskets"],
            labor_hours=5.0, source_url="https://www.bmw-tsb.com",
            published_date="2021-08-15", last_updated="2021-08-15",
        ),
        TSBEntry(
            tsb_id="TSB-2020-010", title="Alternator Bearing Noise",
            description="Some vehicles may exhibit a whining or grinding noise from the alternator.",
            make="Honda", model="Accord", year_start=2013, year_end=2017,
            engine_codes=["2.4L", "3.5L"], related_dtcs=["P0562", "P0620"],
            systems=["electrical"], symptoms=["whining noise", "battery light", "electrical issues"],
            root_cause="Alternator bearing wear",
            repair_procedure="1. Verify noise source\n2. Test alternator output\n3. Replace alternator\n4. Check battery",
            parts_required=["Alternator", "Drive belt"],
            labor_hours=1.5, source_url="https://www.honda.com/TSB",
            published_date="2020-05-20", last_updated="2020-05-20",
        ),
    ]

    def __init__(self, tsb_json_path: str = None):
        self.tsbs: Dict[str, TSBEntry] = {}
        self._load_sample_data()
        if tsb_json_path and os.path.exists(tsb_json_path):
            self.import_from_json(tsb_json_path)

    def _load_sample_data(self):
        for tsb in self.SAMPLE_TSBS:
            self.tsbs[tsb.tsb_id] = tsb
        print(f"[TSBManager] Loaded {len(self.tsbs)} sample TSBs")

    def _filtered(self, make, model, year):
        for tsb in self.tsbs.values():
            if make  and tsb.make.lower()  != make.lower():  continue
            if model and tsb.model.lower() != model.lower(): continue
            if year  and not (tsb.year_start <= year <= tsb.year_end): continue
            yield tsb

    def search_by_codes(self, codes, vehicle_make=None, vehicle_model=None, vehicle_year=None):
        code_set = {c.upper().strip() for c in codes}
        matches = []
        for tsb in self._filtered(vehicle_make, vehicle_model, vehicle_year):
            matched = code_set & set(tsb.related_dtcs)
            if matched:
                score = len(matched) / max(len(code_set), len(tsb.related_dtcs))
                matches.append(TSBMatch(tsb=tsb, match_score=score,
                    matched_codes=list(matched), matched_symptoms=[],
                    reason=f"Matched {len(matched)} trouble code(s)"))
        matches.sort(key=lambda x: x.match_score, reverse=True)
        return matches

    def search_by_symptoms(self, symptoms, vehicle_make=None, vehicle_model=None, vehicle_year=None):
        words = set(symptoms.lower().split())
        matches = []
        for tsb in self._filtered(vehicle_make, vehicle_model, vehicle_year):
            tsb_syms = {s.lower() for s in tsb.symptoms}
            matched_syms = list(words & tsb_syms)
            title_overlap = len(words & set(tsb.title.lower().split()))
            desc_overlap  = len(words & set(tsb.description.lower().split()))
            score = (len(matched_syms)*0.4 + title_overlap*0.3 + desc_overlap*0.1) / max(len(words), 1)
            if score > 0:
                matches.append(TSBMatch(tsb=tsb, match_score=min(score, 1.0),
                    matched_codes=[], matched_symptoms=matched_syms,
                    reason=f"Matched {len(matched_syms)} symptom(s)"))
        matches.sort(key=lambda x: x.match_score, reverse=True)
        return matches

    def search_comprehensive(self, codes=None, symptoms=None,
                             vehicle_make=None, vehicle_model=None, vehicle_year=None):
        matches = []
        for tsb in self._filtered(vehicle_make, vehicle_model, vehicle_year):
            score, reasons, matched_codes, matched_syms = 0.0, [], [], []
            if codes:
                code_set = {c.upper().strip() for c in codes}
                mc = list(code_set & set(tsb.related_dtcs))
                if mc:
                    score += (len(mc) / max(len(code_set), len(tsb.related_dtcs))) * 0.5
                    reasons.append(f"Codes: {', '.join(mc)}")
                    matched_codes = mc
            if symptoms:
                words = set(symptoms.lower().split())
                ms = list(words & {s.lower() for s in tsb.symptoms})
                sym_score = (len(ms)*0.4 + len(words & set(tsb.title.lower().split()))*0.3 +
                             len(words & set(tsb.description.lower().split()))*0.1) / max(len(words), 1)
                if sym_score > 0:
                    score += min(sym_score, 0.5)
                    reasons.append(f"Symptoms: {len(ms)} matches")
                    matched_syms = ms
            if vehicle_make and tsb.make.lower() == vehicle_make.lower(): score += 0.1
            if vehicle_model and tsb.model.lower() == vehicle_model.lower(): score += 0.1
            if score > 0:
                matches.append(TSBMatch(tsb=tsb, match_score=min(score, 1.0),
                    matched_codes=matched_codes, matched_symptoms=matched_syms,
                    reason="; ".join(reasons)))
        matches.sort(key=lambda x: x.match_score, reverse=True)
        return matches

    def get_tsb_by_id(self, tsb_id): return self.tsbs.get(tsb_id)
    def get_tsbs_by_system(self, system): return [t for t in self.tsbs.values() if system.lower() in [s.lower() for s in t.systems]]
    def get_tsbs_by_make(self, make): return [t for t in self.tsbs.values() if t.make.lower() == make.lower()]
    def add_tsb(self, tsb): self.tsbs[tsb.tsb_id] = tsb

    def export_to_json(self, filepath):
        with open(filepath, 'w') as f:
            json.dump([asdict(t) for t in self.tsbs.values()], f, indent=2)

    def import_from_json(self, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        for item in data:
            tsb = TSBEntry(**item)
            self.tsbs[tsb.tsb_id] = tsb


_tsb_manager: Optional[TSBManager] = None

def get_tsb_manager() -> TSBManager:
    global _tsb_manager
    if _tsb_manager is None:
        _tsb_manager = TSBManager()
    return _tsb_manager