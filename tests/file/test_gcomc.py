from pathlib import Path
from urllib.request import urlretrieve

import pytest

from gportal.file import GCOMCFile


class TestGCOMCFile:
    @pytest.fixture
    def eqr_file_path(self):
        filename = "GC1SG1_20230101D01M_D0000_3MSG_SST_F_3000.h5"
        path = Path(__file__).parent / f"fixture/{filename}"
        if not path.exists():
            urlretrieve(
                f"ftp://sankichi92:anonymous@ftp.gportal.jaxa.jp/standard/GCOM-C/GCOM-C.SGLI/L3.OCEAN.SST_/3/2023/01/{filename}",
                path,
            )
        return path

    def test_save_as_geotiff(self, eqr_file_path, tmp_path):
        # Given
        file = GCOMCFile.open(eqr_file_path)

        # When
        output_paths = file.save_as_geotiff(output_dir=tmp_path)
        file.close()

        # Then
        for path in output_paths:
            assert Path(path).exists()
