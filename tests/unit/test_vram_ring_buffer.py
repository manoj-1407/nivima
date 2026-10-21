"""Unit tests for Patent Pillar 1: VRAM Ring-Buffer Apparatus."""
from src.hardware.vram_ring_buffer import VRAMRingBufferManager, get_vram_ring_buffer


def test_ring_buffer_initialization():
    mgr = VRAMRingBufferManager(target_pool_mb=512)
    telemetry = mgr.get_hardware_telemetry()
    assert telemetry.total_vram_bytes == 512 * 1024 * 1024
    assert telemetry.active_partitions == 0


def test_partition_provision_and_reuse():
    mgr = VRAMRingBufferManager(target_pool_mb=1024)

    # Stage 1: Whisper ASR
    p1 = mgr.provision_partition("whisper_asr", required_mb=256)
    assert p1.partition_id == "whisper_asr"
    assert p1.size_bytes == 256 * 1024 * 1024

    # Stage 2: Reuse existing partition without fresh allocation
    p1_reused = mgr.provision_partition("whisper_asr", required_mb=256)
    assert p1_reused.offset_bytes == p1.offset_bytes
    telemetry = mgr.get_hardware_telemetry()
    assert telemetry.dynamic_allocations_prevented >= 2
    assert telemetry.pcie_bytes_saved >= 256 * 1024 * 1024


def test_lock_and_eviction_under_pressure():
    # Small pool to trigger eviction logic
    mgr = VRAMRingBufferManager(target_pool_mb=200)

    mgr.provision_partition("p1", required_mb=100)
    mgr.provision_partition("p2", required_mb=80)
    # Lock p2
    mgr.lock_partition("p2", "active_model")

    # Allocate p3 which forces eviction of unlocked p1
    mgr.provision_partition("p3", required_mb=50)

    # p2 should still be present because it was locked
    assert "p2" in mgr.partitions


def test_singleton_accessor():
    b1 = get_vram_ring_buffer()
    b2 = get_vram_ring_buffer()
    assert b1 is b2
