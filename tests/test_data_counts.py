import unittest
from pathlib import Path

class TestJobDataConsistency(unittest.TestCase):
    """Test that job_blocks and job_data have the same number of files"""

    @classmethod
    def setUpClass(cls):
        # Go from tests/ folder up to project root
        cls.project_root = Path(__file__).parent.parent
        cls.data_dir = cls.project_root / "data"

    def test_job_blocks_and_job_data_have_same_file_count(self):
        """Ensure every filtered job has a corresponding JSON file"""
        job_blocks_dir = self.data_dir / "job_blocks"
        job_data_dir = self.data_dir / "job_data"

        count_blocks = self._count_files(job_blocks_dir)
        count_data = self._count_files(job_data_dir)

        print(f"\n📂 job_blocks: {count_blocks} files")
        print(f"📂 job_data:   {count_data} files")

        # ✅ Core assertion: they MUST be equal
        self.assertEqual(
            count_blocks,
            count_data,
            f"❌ Mismatch: job_blocks ({count_blocks}) != job_data ({count_data})"
        )

    def _count_files(self, folder: Path) -> int:
        """Count only files (ignore subfolders)"""
        if not folder.exists():
            return 0
        return len([f for f in folder.iterdir() if f.is_file()])

if __name__ == '__main__':
    unittest.main(verbosity=2)