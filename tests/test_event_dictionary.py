import yaml, os, pytest

@pytest.fixture
def event_dict():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configs', 'event_dict_v1.yaml')
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def test_yaml_loads(event_dict):
    assert event_dict is not None

def test_version_present(event_dict):
    assert 'version' in event_dict
    assert event_dict['version'] == 'event_dict_v1'

def test_status_present(event_dict):
    assert 'status' in event_dict

def test_support_components_defined(event_dict):
    sc = event_dict['support_components']
    assert 'vasopressors' in sc
    assert 'invasive_ventilation' in sc

def test_vasopressor_agents_defined(event_dict):
    agents = event_dict['support_components']['vasopressors']['qualifying_agents']
    assert isinstance(agents, list)
    assert len(agents) >= 3

def test_ventilation_modes_defined(event_dict):
    modes = event_dict['support_components']['invasive_ventilation']
    assert 'qualifying_modes' in modes
    assert 'non_qualifying_modes' in modes

def test_state_definitions(event_dict):
    assert 'ON' in event_dict['state_definitions']
    assert 'OFF' in event_dict['state_definitions']

def test_censoring_rules(event_dict):
    assert 'censoring_rules' in event_dict
    rules = event_dict['censoring_rules']['rules']
    assert len(rules) >= 3

def test_interval_convention(event_dict):
    assert 'interval_convention' in event_dict
    assert event_dict['interval_convention']['notation'] == '(t, t + 24h]'

def test_provenance(event_dict):
    assert 'provenance' in event_dict
    assert event_dict['provenance']['clinical_validity'] is False

def test_freeze_discipline(event_dict):
    assert 'freeze_discipline' in event_dict
