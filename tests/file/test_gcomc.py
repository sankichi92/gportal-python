from pathlib import Path
from urllib.request import urlretrieve

import pytest

from gportal.file import GCOMCFile


class TestGCOMCFile:
    @pytest.fixture
    def l3_sst_eqr(self):
        filename = "GC1SG1_20230101D01M_D0000_3MSG_SST_F_3000.h5"
        path = Path(__file__).parent / f"fixture/{filename}"
        if not path.exists():
            urlretrieve(
                f"ftp://sankichi92:anonymous@ftp.gportal.jaxa.jp/standard/GCOM-C/GCOM-C.SGLI/L3.OCEAN.SST_/3/2023/01/{filename}",
                path,
            )
        return path

    @pytest.fixture
    def l2_rsrf_eqa(self):
        filename = "GC1SG1_20230501D01D_T0529_L2SG_RSRFQ_3002.h5"
        path = Path(__file__).parent / f"fixture/{filename}"
        if not path.exists():
            urlretrieve(
                f"ftp://sankichi92:anonymous@ftp.gportal.jaxa.jp/standard/GCOM-C/GCOM-C.SGLI/L2.LAND.RSRF/3/2023/05/01/{filename}",
                path,
            )
        return path

    def test_save_as_geotiff(self, l3_sst_eqr, tmp_path):
        # Given
        file = GCOMCFile.open(l3_sst_eqr)

        # When
        output_path_map = file.save_as_geotiff(output_dir=tmp_path)
        file.close()

        # Then
        for _, path in output_path_map.items():
            assert Path(path).exists()

    def test_save_as_multiband_geotiff(self, l2_rsrf_eqa, tmp_path):
        # Given
        file = GCOMCFile.open(l2_rsrf_eqa)

        # When
        output_path = tmp_path / f"{file.granule_id}.tif"
        file.save_as_multiband_geotiff(bands=["Rs_VN08", "Rs_VN05", "Rs_VN03"], output_path=output_path)
        file.close()

        # Then
        assert Path(output_path).exists()
