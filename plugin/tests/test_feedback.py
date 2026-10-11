"""Structured host feedback is optional for old hosts, authoritative results are not."""
import threading

import pytest

pytest.importorskip('sparkrun.feedback')
from sparkrun.core.operation import OperationState, operation_scope
from sparkrun.plugins import get_feedback
from sparkrun_oci_relay.progress import Progress
from sparkrun_oci_relay.parallel import parallel


@pytest.mark.parametrize('valid', [True, False])
def test_transfer_counters_and_verification_outcome(valid, caplog):
    caplog.set_level(25)
    seen = []
    with operation_scope(state=OperationState(events=seen.append)):
        p = Progress('image', interval=0)
        p.bind({'r': 'host-a'})
        try:
            p.event({'receiver_progress': {'r': {'sequence': 1, 'phase': 'transferring', 'inventory_ready': True,
                'received_bytes': 4, 'expected_bytes': 4, 'bytes_per_second': 2, 'reused_layers': 1}}})
            p.outcome('r', {'progress': {'wire_bytes': 4}}, valid)
        finally:
            p.close(valid, False)
    events = [v for v in seen if v['type'] == 'feedback']
    transfer = next(v for v in events if v.get('stage') == 'transferring')
    assert transfer['current'] == transfer['total'] == 4
    assert transfer['total_kind'] == 'upper_bound' and transfer['status'] == 'running'
    assert transfer['host'] == 'host-a' and transfer['metrics']['bytes_per_second'] == 2
    verified = next(v for v in events if v.get('stage') == 'verify')
    assert verified['activity_id'] == transfer['activity_id']
    assert verified['status'] == ('succeeded' if valid else 'failed')
    assert events[-1]['status'] == verified['status']
    assert len(seen) == len(events) == len(caplog.records)


def test_heartbeat_and_parallel_work_retain_operation():
    seen = []
    heartbeat = threading.Event()
    def receive(event):
        seen.append(event)
        if event.get('metrics', {}).get('heartbeat'):
            heartbeat.set()
    with operation_scope(state=OperationState(id='transfer', events=receive)):
        p = Progress('image', heartbeat=0.01)
        try:
            assert heartbeat.wait(2)
            parallel(['host-a', 'host-b'], lambda host: get_feedback('oci-relay').progress('checking', host=host))
        finally:
            p.close(False, False)
    assert all(v['operation_id'] == 'transfer' for v in seen)
    assert {v.get('host') for v in seen if v['message'] == 'checking'} == {'host-a', 'host-b'}


def test_older_host_keeps_text_output(monkeypatch, caplog):
    import sparkrun.plugins
    monkeypatch.delattr(sparkrun.plugins, 'get_feedback')
    caplog.set_level(25)
    p = Progress('old-host-image')
    p.close(False, False)
    assert 'preparing old-host-image' in caplog.text
