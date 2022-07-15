import json
from datetime import datetime

import pytest

from telliot_feeds.sources.morphware import MorphwareV1Source


@pytest.mark.asyncio
async def test_fetch_new_datapoint():
    """Retrieve EC2 metadata."""
    v, t = await MorphwareV1Source().fetch_new_datapoint()

    assert v is not None and t is not None
    assert isinstance(v, list)
    assert isinstance(t, datetime)
    assert isinstance(v[0], str)

    assert len(v) == 21
    for metadata_str in v:
        ec2_dict = json.loads(metadata_str)
        assert "Instance Type" in ec2_dict
        assert "CUDA Cores" in ec2_dict
        assert "Number of CPUs" in ec2_dict
        assert "RAM" in ec2_dict
        assert "On-demand Price per Hour" in ec2_dict

        assert isinstance(ec2_dict["Instance Type"], str)
        assert isinstance(ec2_dict["CUDA Cores"], int)
        assert isinstance(ec2_dict["Number of CPUs"], int)
        assert isinstance(ec2_dict["RAM"], float)
        assert isinstance(ec2_dict["On-demand Price per Hour"], float)


EXAMPLE_RESPONSE = [
    {
        "Instance Type": "p2.16xlarge",
        "CUDA Cores": 79872,
        "Number of CPUs": 64,
        "RAM": 732.0,
        "On-demand Price per Hour": 14.4,
    },
    {
        "Instance Type": "p2.8xlarge",
        "CUDA Cores": 39936,
        "Number of CPUs": 32,
        "RAM": 488.0,
        "On-demand Price per Hour": 7.2,
    },
    {
        "Instance Type": "p2.xlarge",
        "CUDA Cores": 4992,
        "Number of CPUs": 4,
        "RAM": 61.0,
        "On-demand Price per Hour": 0.9,
    },
    {
        "Instance Type": "g3s.xlarge",
        "CUDA Cores": 4096,
        "Number of CPUs": 4,
        "RAM": 30.5,
        "On-demand Price per Hour": 0.75,
    },
    {
        "Instance Type": "g4dn.xlarge",
        "CUDA Cores": 2560,
        "Number of CPUs": 4,
        "RAM": 16.0,
        "On-demand Price per Hour": 0.526,
    },
    {
        "Instance Type": "g3.16xlarge",
        "CUDA Cores": 16384,
        "Number of CPUs": 64,
        "RAM": 488.0,
        "On-demand Price per Hour": 4.56,
    },
    {
        "Instance Type": "g3.4xlarge",
        "CUDA Cores": 4096,
        "Number of CPUs": 16,
        "RAM": 122.0,
        "On-demand Price per Hour": 1.14,
    },
    {
        "Instance Type": "g3.8xlarge",
        "CUDA Cores": 8192,
        "Number of CPUs": 32,
        "RAM": 244.0,
        "On-demand Price per Hour": 2.28,
    },
    {
        "Instance Type": "g4dn.2xlarge",
        "CUDA Cores": 2560,
        "Number of CPUs": 8,
        "RAM": 32.0,
        "On-demand Price per Hour": 0.752,
    },
    {
        "Instance Type": "g4dn.12xlarge",
        "CUDA Cores": 10240,
        "Number of CPUs": 48,
        "RAM": 192.0,
        "On-demand Price per Hour": 3.912,
    },
    {
        "Instance Type": "g4dn.metal",
        "CUDA Cores": 20480,
        "Number of CPUs": 96,
        "RAM": 384.0,
        "On-demand Price per Hour": 7.824,
    },
    {
        "Instance Type": "g2.2xlarge",
        "CUDA Cores": 1536,
        "Number of CPUs": 8,
        "RAM": 15.0,
        "On-demand Price per Hour": 0.65,
    },
    {
        "Instance Type": "g2.8xlarge",
        "CUDA Cores": 6144,
        "Number of CPUs": 32,
        "RAM": 60.0,
        "On-demand Price per Hour": 2.6,
    },
    {
        "Instance Type": "g4dn.4xlarge",
        "CUDA Cores": 2560,
        "Number of CPUs": 16,
        "RAM": 64.0,
        "On-demand Price per Hour": 1.204,
    },
    {
        "Instance Type": "p4d.24xlarge",
        "CUDA Cores": 55296,
        "Number of CPUs": 96,
        "RAM": 1152.0,
        "On-demand Price per Hour": 32.7726,
    },
    {
        "Instance Type": "p3.16xlarge",
        "CUDA Cores": 40960,
        "Number of CPUs": 64,
        "RAM": 488.0,
        "On-demand Price per Hour": 24.48,
    },
    {
        "Instance Type": "p3.2xlarge",
        "CUDA Cores": 5120,
        "Number of CPUs": 8,
        "RAM": 61.0,
        "On-demand Price per Hour": 3.06,
    },
    {
        "Instance Type": "p3.8xlarge",
        "CUDA Cores": 20480,
        "Number of CPUs": 32,
        "RAM": 244.0,
        "On-demand Price per Hour": 12.24,
    },
    {
        "Instance Type": "p3dn.24xlarge",
        "CUDA Cores": 40960,
        "Number of CPUs": 96,
        "RAM": 768.0,
        "On-demand Price per Hour": 31.212,
    },
    {
        "Instance Type": "g4dn.8xlarge",
        "CUDA Cores": 2560,
        "Number of CPUs": 32,
        "RAM": 128.0,
        "On-demand Price per Hour": 2.176,
    },
    {
        "Instance Type": "g4dn.16xlarge",
        "CUDA Cores": 2560,
        "Number of CPUs": 64,
        "RAM": 256.0,
        "On-demand Price per Hour": 4.352,
    },
]
