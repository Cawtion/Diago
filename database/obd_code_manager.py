"""
OBD Code Manager - Enhanced with Free Database Integration
Provides fast lookup, pattern matching, and cross-referencing.
Integrates with Diago's existing database layer.
"""
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class OBDCodeInfo:
    """Structured OBD code information."""
    code: str
    description: str
    category: str       # P0, P1, P2, P3, B, C, U
    severity: str       # low, medium, high, critical
    system: str         # engine, transmission, body, chassis, network
    symptoms: List[str]
    common_causes: List[str]
    related_codes: List[str]


class OBDCodeManager:
    """
    Manages OBD trouble codes with pattern recognition and cross-referencing.
    Expects the OBD JSON database at:  data/obd_codes/obd2_complete.json
    (relative to the Diago repo root).
    """

    CATEGORY_PATTERNS = {
        'P0': {'name': 'Generic Powertrain',                    'severity': 'medium'},
        'P1': {'name': 'Manufacturer Specific Powertrain',      'severity': 'high'},
        'P2': {'name': 'Generic Powertrain (Extended)',         'severity': 'medium'},
        'P3': {'name': 'Generic Powertrain (Reserved)',         'severity': 'medium'},
        'B0': {'name': 'Generic Body',                          'severity': 'low'},
        'B1': {'name': 'Manufacturer Specific Body',            'severity': 'medium'},
        'B2': {'name': 'Generic Body (Reserved)',               'severity': 'low'},
        'B3': {'name': 'Generic Body (Reserved)',               'severity': 'low'},
        'C0': {'name': 'Generic Chassis',                       'severity': 'medium'},
        'C1': {'name': 'Manufacturer Specific Chassis',         'severity': 'high'},
        'C2': {'name': 'Generic Chassis (Reserved)',            'severity': 'medium'},
        'C3': {'name': 'Generic Chassis (Reserved)',            'severity': 'medium'},
        'U0': {'name': 'Generic Network',                       'severity': 'high'},
        'U1': {'name': 'Manufacturer Specific Network',         'severity': 'high'},
        'U2': {'name': 'Generic Network (Reserved)',            'severity': 'high'},
        'U3': {'name': 'Generic Network (Reserved)',            'severity': 'high'},
    }

    CODE_PATTERNS = {
        'both_banks_lean': {
            'codes': ['P0171', 'P0174'],
            'description': 'System too lean on both banks',
            'likely_cause': 'Vacuum leak, MAF sensor, fuel pressure, or O2 sensors',
            'confidence': 0.92,
        },
        'both_banks_rich': {
            'codes': ['P0172', 'P0175'],
            'description': 'System too rich on both banks',
            'likely_cause': 'Faulty fuel injectors, MAF sensor, fuel pressure regulator, or thermostat',
            'confidence': 0.90,
        },
        'multiple_misfire': {
            'codes': ['P0300'],
            'description': 'Random/Multiple Cylinder Misfire Detected',
            'likely_cause': 'Ignition system, fuel system, vacuum leak, or mechanical issue',
            'confidence': 0.85,
        },
        'single_cylinder_misfire': {
            'codes': ['P0301', 'P0302', 'P0303', 'P0304', 'P0305', 'P0306', 'P0307', 'P0308'],
            'description': 'Specific cylinder misfire',
            'likely_cause': 'Spark plug, ignition coil, fuel injector, or compression issue',
            'confidence': 0.88,
        },
        'evap_leak_large': {
            'codes': ['P0455'],
            'description': 'EVAP System Large Leak Detected',
            'likely_cause': 'Loose gas cap, damaged EVAP lines, or faulty purge valve',
            'confidence': 0.90,
        },
        'evap_leak_small': {
            'codes': ['P0456'],
            'description': 'EVAP System Small Leak Detected',
            'likely_cause': 'Minor leak in EVAP system, often gas cap related',
            'confidence': 0.85,
        },
        'catalyst_efficiency_bank1': {
            'codes': ['P0420'],
            'description': 'Catalyst System Efficiency Below Threshold (Bank 1)',
            'likely_cause': 'Failing catalytic converter, O2 sensors, or exhaust leak',
            'confidence': 0.87,
        },
        'catalyst_efficiency_bank2': {
            'codes': ['P0430'],
            'description': 'Catalyst System Efficiency Below Threshold (Bank 2)',
            'likely_cause': 'Failing catalytic converter, O2 sensors, or exhaust leak',
            'confidence': 0.87,
        },
        'o2_sensor_slow_response': {
            'codes': ['P0133', 'P0153'],
            'description': 'O2 Sensor Slow Response',
            'likely_cause': 'Aging O2 sensor, exhaust leak, or fuel mixture issue',
            'confidence': 0.82,
        },
        'maf_sensor': {
            'codes': ['P0100', 'P0101', 'P0102', 'P0103', 'P0104'],
            'description': 'Mass Air Flow Sensor Circuit Issue',
            'likely_cause': 'Dirty/faulty MAF sensor, wiring, or air leak',
            'confidence': 0.87,
        },
        'vvt_system': {
            'codes': ['P0010', 'P0011', 'P0012', 'P0013', 'P0014', 'P0015'],
            'description': 'Variable Valve Timing System Issue',
            'likely_cause': 'Faulty VVT solenoid, oil pressure issue, or timing component wear',
            'confidence': 0.85,
        },
        'ignition_coil_primary': {
            'codes': ['P0351', 'P0352', 'P0353', 'P0354', 'P0355', 'P0356', 'P0357', 'P0358'],
            'description': 'Ignition Coil Primary/Secondary Circuit Issue',
            'likely_cause': 'Faulty ignition coil, wiring, or PCM driver',
            'confidence': 0.90,
        },
        'crankshaft_position': {
            'codes': ['P0335', 'P0336', 'P0337', 'P0338', 'P0339'],
            'description': 'Crankshaft Position Sensor Circuit Issue',
            'likely_cause': 'Faulty CKP sensor, wiring, or reluctor ring damage',
            'confidence': 0.90,
        },
        'egr_system': {
            'codes': ['P0400', 'P0401', 'P0402', 'P0403', 'P0404', 'P0405'],
            'description': 'Exhaust Gas Recirculation System Issue',
            'likely_cause': 'Clogged EGR valve, faulty EGR solenoid, or carbon buildup',
            'confidence': 0.84,
        },
        'boost_pressure': {
            'codes': ['P0234', 'P0235', 'P0236', 'P0237', 'P0238'],
            'description': 'Turbocharger/Supercharger Boost System Issue',
            'likely_cause': 'Faulty boost sensor, wastegate, boost leak, or turbo failure',
            'confidence': 0.85,
        },
        'knock_sensor': {
            'codes': ['P0325', 'P0326', 'P0327', 'P0328'],
            'description': 'Knock Sensor Circuit Issue',
            'likely_cause': 'Faulty knock sensor, wiring, or excessive engine knock',
            'confidence': 0.85,
        },
        'fuel_injector_circuit': {
            'codes': ['P0201', 'P0202', 'P0203', 'P0204', 'P0205', 'P0206', 'P0207', 'P0208'],
            'description': 'Fuel Injector Circuit Issue',
            'likely_cause': 'Faulty fuel injector, wiring, or PCM driver',
            'confidence': 0.88,
        },
        'alternator_field': {
            'codes': ['P0620', 'P0621', 'P0622'],
            'description': 'Generator Field/F Terminal Circuit Issue',
            'likely_cause': 'Faulty alternator, voltage regulator, or wiring',
            'confidence': 0.87,
        },
    }

    def __init__(self, database_path: str = None):
        if database_path is None:
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            database_path = os.path.join(repo_root, 'data', 'obd_codes', 'obd2_complete.json')

        self.database_path = database_path
        self.codes: Dict[str, str] = {}
        self.code_info: Dict[str, OBDCodeInfo] = {}

        self._load_database()
        self._build_enhanced_index()

    def _load_database(self):
        try:
            with open(self.database_path, 'r') as f:
                self.codes = json.load(f)
            print(f"[OBDCodeManager] Loaded {len(self.codes)} codes from {self.database_path}")
        except FileNotFoundError:
            print(f"[OBDCodeManager] WARNING: database not found at {self.database_path}.")
            self.codes = {}
        except json.JSONDecodeError as e:
            print(f"[OBDCodeManager] ERROR parsing database: {e}")
            self.codes = {}

    def _build_enhanced_index(self):
        for code, description in self.codes.items():
            self.code_info[code] = OBDCodeInfo(
                code=code,
                description=description,
                category=self._get_category(code),
                severity=self._infer_severity(code, description),
                system=self._infer_system(code, description),
                symptoms=self._extract_symptoms(description),
                common_causes=self._infer_common_causes(code, description),
                related_codes=self._find_related_codes(code),
            )

    def _get_category(self, code: str) -> str:
        return code[:2] if len(code) >= 2 else code[:1]

    def _infer_severity(self, code: str, description: str) -> str:
        cat_info = self.CATEGORY_PATTERNS.get(self._get_category(code), {'severity': 'medium'})
        desc = description.lower()
        if any(k in desc for k in ('catalyst', 'misfire', 'knock', 'overheat', 'fuel pressure')):
            return 'critical'
        if cat_info['severity'] == 'high':
            return 'high'
        if any(k in desc for k in ('circuit', 'sensor', 'valve', 'injector')):
            return 'high'
        return cat_info['severity']

    def _infer_system(self, code: str, description: str) -> str:
        desc = description.lower()
        if code.startswith('P'):
            if any(x in desc for x in ('transmission', 'torque converter', 'gear')):
                return 'transmission'
            if any(x in desc for x in ('evap', 'emission', 'catalyst', 'egr', 'air injection')):
                return 'emissions'
            if any(x in desc for x in ('fuel', 'injector', 'pump', 'pressure')):
                return 'fuel_system'
            if any(x in desc for x in ('ignition', 'coil', 'spark', 'misfire')):
                return 'ignition'
            return 'engine'
        return {'B': 'body', 'C': 'chassis', 'U': 'network'}.get(code[0], 'unknown')

    def _extract_symptoms(self, description: str) -> List[str]:
        symptom_map = {
            'misfire':  ['rough idle', 'loss of power', 'vibration'],
            'lean':     ['hesitation', 'poor acceleration', 'stalling'],
            'rich':     ['black smoke', 'fuel smell', 'poor fuel economy'],
            'catalyst': ['check engine light', 'failed emissions', 'rotten egg smell'],
            'sensor':   ['erratic behavior', 'poor performance', 'check engine light'],
            'circuit':  ['intermittent issue', 'complete failure', 'warning light'],
            'pressure': ['performance issue', 'noise', 'warning light'],
        }
        desc = description.lower()
        symptoms = []
        for kw, syms in symptom_map.items():
            if kw in desc:
                symptoms.extend(syms)
        return list(set(symptoms))

    def _infer_common_causes(self, code: str, description: str) -> List[str]:
        causes = []
        desc = description.lower()
        for pattern in self.CODE_PATTERNS.values():
            if code in pattern['codes']:
                causes.append(pattern['likely_cause'])
        if 'sensor' in desc:
            causes += ['Faulty sensor', 'Wiring issue']
        if 'circuit' in desc:
            causes += ['Open or short in wiring', 'Poor electrical connection']
        if 'pressure' in desc:
            causes += ['Mechanical failure', 'Leak or blockage']
        return causes

    def _find_related_codes(self, code: str) -> List[str]:
        related = []
        for pattern in self.CODE_PATTERNS.values():
            if code in pattern['codes']:
                related.extend(c for c in pattern['codes'] if c != code)
        if len(code) >= 5 and code[-2:].isdigit():
            base, num = code[:-2], int(code[-2:])
            for offset in (-1, 1):
                adj = f"{base}{num + offset:02d}"
                if adj in self.codes and adj != code:
                    related.append(adj)
        return list(set(related))

    def lookup(self, code: str) -> Optional[OBDCodeInfo]:
        return self.code_info.get(code.upper().strip())

    def lookup_multiple(self, codes: List[str]) -> Dict[str, OBDCodeInfo]:
        return {c: self.lookup(c) for c in codes if self.lookup(c)}

    def detect_patterns(self, codes: List[str]) -> List[dict]:
        code_set = {c.upper().strip() for c in codes}
        detected = []
        for name, info in self.CODE_PATTERNS.items():
            pattern_codes = set(info['codes'])
            matched = code_set & pattern_codes
            if matched:
                ratio = len(matched) / len(pattern_codes)
                detected.append({
                    'pattern_name': name,
                    'description': info['description'],
                    'matched_codes': list(matched),
                    'all_pattern_codes': info['codes'],
                    'likely_cause': info['likely_cause'],
                    'confidence': info['confidence'] * (0.5 + 0.5 * ratio),
                    'match_ratio': ratio,
                })
        detected.sort(key=lambda x: x['confidence'], reverse=True)
        return detected

    def get_test_sequence(self, codes: List[str]) -> List[dict]:
        tests = []
        for p in self.detect_patterns(codes):
            if p['confidence'] > 0.7:
                tests.append({
                    'priority': 'HIGH',
                    'test': f"Investigate {p['description']}",
                    'focus': p['likely_cause'],
                    'confidence': p['confidence'],
                })
        for code in codes:
            info = self.lookup(code)
            if info:
                tests.append({
                    'priority': 'MEDIUM',
                    'test': f"Test {code}: {info.description}",
                    'focus': ', '.join(info.common_causes[:2]) or 'Component testing',
                    'confidence': 0.7,
                })
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        tests.sort(key=lambda x: (priority_order.get(x['priority'], 3), -x['confidence']))
        return tests

    def search_by_symptom(self, symptom: str) -> List[OBDCodeInfo]:
        symptom_lower = symptom.lower()
        matches = []
        for info in self.code_info.values():
            if symptom_lower in info.description.lower():
                matches.append(info)
            elif any(symptom_lower in s.lower() for s in info.symptoms):
                matches.append(info)
        return matches

    def get_codes_by_system(self, system: str) -> List[OBDCodeInfo]:
        return [i for i in self.code_info.values() if i.system == system.lower()]

    def get_codes_by_severity(self, severity: str) -> List[OBDCodeInfo]:
        return [i for i in self.code_info.values() if i.severity == severity.lower()]

    def analyze_code_combination(self, codes: List[str]) -> dict:
        code_infos = self.lookup_multiple(codes)
        patterns = self.detect_patterns(codes)
        test_sequence = self.get_test_sequence(codes)

        systems: Dict[str, int] = defaultdict(int)
        for info in code_infos.values():
            systems[info.system] += 1
        primary_system = max(systems, key=systems.get) if systems else 'unknown'

        severity_priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        severities = [info.severity for info in code_infos.values()]
        max_severity = (
            max(severities, key=lambda s: severity_priority.get(s, 0))
            if severities else 'unknown'
        )

        overall_confidence = max((p['confidence'] for p in patterns), default=0.5)

        return {
            'codes_analyzed': len(code_infos),
            'primary_system': primary_system,
            'overall_severity': max_severity,
            'detected_patterns': patterns,
            'recommended_tests': test_sequence,
            'overall_confidence': overall_confidence,
            'requires_immediate_attention': max_severity == 'critical',
        }


_obd_manager: Optional[OBDCodeManager] = None

def get_obd_manager() -> OBDCodeManager:
    global _obd_manager
    if _obd_manager is None:
        _obd_manager = OBDCodeManager()
    return _obd_manager