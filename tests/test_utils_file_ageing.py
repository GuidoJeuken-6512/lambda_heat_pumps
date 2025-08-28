"""Tests für die Datei-Alterung-Hilfsfunktionen in utils.py."""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from homeassistant.core import HomeAssistant
from custom_components.lambda_heat_pumps.utils import (
    analyze_file_ageing,
    analyze_single_file_ageing,
    delete_files
)


class TestFileAgeingFunctions:
    """Test-Klasse für die Datei-Alterung-Funktionen."""
    
    @pytest.fixture
    def temp_dir(self):
        """Erstelle ein temporäres Verzeichnis für Tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_hass(self):
        """Erstelle einen Mock für Home Assistant."""
        hass = Mock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        return hass
    
    def mock_os_listdir(self, directory):
        """Mock für os.listdir."""
        import os
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    def create_test_file(self, temp_dir: str, filename: str, days_old: int = 0):
        """Erstelle eine Test-Datei mit bestimmtem Alter."""
        file_path = os.path.join(temp_dir, filename)
        
        # Erstelle Datei mit bestimmtem Alter
        with open(file_path, 'w') as f:
            f.write("test content")
        
        # Setze das Datum der Datei
        if days_old > 0:
            old_time = datetime.now() - timedelta(days=days_old)
            os.utime(file_path, (old_time.timestamp(), old_time.timestamp()))
        
        return file_path
    
    @pytest.mark.asyncio
    async def test_analyze_file_ageing_empty_directory(self, mock_hass, temp_dir):
        """Test: Leeres Verzeichnis analysieren."""
        result = await analyze_file_ageing(mock_hass, temp_dir, "")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_analyze_file_ageing_single_file(self, mock_hass, temp_dir):
        """Test: Einzelne Datei analysieren."""
        # Erstelle Test-Datei
        test_file = self.create_test_file(temp_dir, "test.txt", days_old=5)
        
        # Mock os.listdir und os.stat
        mock_hass.async_add_executor_job.side_effect = [
            ["test.txt"],  # os.listdir
            Mock(st_mtime=(datetime.now() - timedelta(days=5)).timestamp())  # os.stat
        ]
        
        result = await analyze_file_ageing(mock_hass, temp_dir, "")
        
        assert len(result) == 1
        file_path, days_old, error = result[0]
        assert file_path == test_file
        assert days_old == 5
        assert error is None
    
    @pytest.mark.asyncio
    async def test_analyze_file_ageing_with_filename_mask(self, mock_hass, temp_dir):
        """Test: Dateien mit Namensmaske filtern."""
        # Erstelle verschiedene Test-Dateien
        self.create_test_file(temp_dir, "config.yaml", days_old=3)
        self.create_test_file(temp_dir, "backup.txt", days_old=7)
        self.create_test_file(temp_dir, "log.log", days_old=1)
        
        # Mock os.listdir und os.stat für alle Dateien
        mock_hass.async_add_executor_job.side_effect = [
            ["config.yaml", "backup.txt", "log.log"],  # os.listdir
            Mock(st_mtime=(datetime.now() - timedelta(days=3)).timestamp()),  # os.stat
        ]
        
        # Teste mit Namensmaske "config"
        result = await analyze_file_ageing(mock_hass, temp_dir, "config")
        
        assert len(result) == 1
        file_path, days_old, error = result[0]
        assert "config" in file_path
        assert days_old == 3
        assert error is None
    
    @pytest.mark.asyncio
    async def test_analyze_file_ageing_recursive(self, mock_hass, temp_dir):
        """Test: Rekursive Verzeichnissuche."""
        # Erstelle Unterverzeichnis
        sub_dir = os.path.join(temp_dir, "subdir")
        os.makedirs(sub_dir)
        
        # Erstelle Dateien in Haupt- und Unterverzeichnis
        self.create_test_file(temp_dir, "main.txt", days_old=2)
        self.create_test_file(sub_dir, "sub.txt", days_old=4)
        
        # Mock os.stat
        mock_hass.async_add_executor_job.side_effect = [
            Mock(st_mtime=(datetime.now() - timedelta(days=2)).timestamp()),  # main.txt
            Mock(st_mtime=(datetime.now() - timedelta(days=4)).timestamp()),  # sub.txt
        ]
        
        # Teste rekursive Suche
        result = await analyze_file_ageing(mock_hass, temp_dir, "", recursive=True)
        
        assert len(result) == 2
        file_paths = [r[0] for r in result]
        assert any("main.txt" in path for path in file_paths)
        assert any("sub.txt" in path for path in file_paths)
    
    @pytest.mark.asyncio
    async def test_analyze_file_ageing_directory_not_exists(self, mock_hass):
        """Test: Verzeichnis existiert nicht."""
        result = await analyze_file_ageing(mock_hass, "/nonexistent/path", "")
        
        assert len(result) == 1
        file_path, days_old, error = result[0]
        assert file_path == "/nonexistent/path"
        assert days_old == 0
        assert "existiert nicht" in error
    
    @pytest.mark.asyncio
    async def test_analyze_file_ageing_not_directory(self, mock_hass, temp_dir):
        """Test: Pfad ist kein Verzeichnis."""
        # Erstelle eine Datei statt Verzeichnis
        test_file = self.create_test_file(temp_dir, "test.txt")
        
        result = await analyze_file_ageing(mock_hass, test_file, "")
        
        assert len(result) == 1
        file_path, days_old, error = result[0]
        assert file_path == test_file
        assert days_old == 0
        assert "kein Verzeichnis" in error
    
    @pytest.mark.asyncio
    async def test_analyze_single_file_ageing(self, mock_hass, temp_dir):
        """Test: Einzelne Datei analysieren."""
        test_file = self.create_test_file(temp_dir, "single.txt", days_old=10)
        
        # Mock os.stat
        mock_stat = Mock()
        mock_stat.st_mtime = (datetime.now() - timedelta(days=10)).timestamp()
        mock_hass.async_add_executor_job.return_value = mock_stat
        
        result = await analyze_single_file_ageing(mock_hass, test_file)
        
        file_path, days_old, error = result
        assert file_path == test_file
        assert days_old == 10
        assert error is None
    
    @pytest.mark.asyncio
    async def test_analyze_single_file_ageing_not_exists(self, mock_hass):
        """Test: Einzelne Datei existiert nicht."""
        result = await analyze_single_file_ageing(mock_hass, "/nonexistent/file.txt")
        
        file_path, days_old, error = result
        assert file_path == "/nonexistent/file.txt"
        assert days_old == 0
        assert "existiert nicht" in error
    
    @pytest.mark.asyncio
    async def test_delete_files_dry_run(self, mock_hass, temp_dir):
        """Test: Dateien im Dry-Run-Modus löschen."""
        # Erstelle Test-Dateien
        test_files = [
            self.create_test_file(temp_dir, "file1.txt"),
            self.create_test_file(temp_dir, "file2.txt"),
            self.create_test_file(temp_dir, "file3.txt"),
        ]
        
        # Teste Dry-Run (keine echte Löschung)
        deleted_count, errors = await delete_files(mock_hass, test_files, dry_run=True)
        
        assert deleted_count == 3
        assert len(errors) == 0
        
        # Prüfe, dass Dateien noch existieren
        for file_path in test_files:
            assert os.path.exists(file_path)
    
    @pytest.mark.asyncio
    async def test_delete_files_actual_deletion(self, mock_hass, temp_dir):
        """Test: Tatsächliches Löschen von Dateien."""
        # Erstelle Test-Dateien
        test_files = [
            self.create_test_file(temp_dir, "delete1.txt"),
            self.create_test_file(temp_dir, "delete2.txt"),
        ]
        
        # Teste tatsächliche Löschung
        deleted_count, errors = await delete_files(mock_hass, test_files, dry_run=False)
        
        assert deleted_count == 2
        assert len(errors) == 0
        
        # Prüfe, dass Dateien gelöscht wurden
        for file_path in test_files:
            assert not os.path.exists(file_path)
    
    @pytest.mark.asyncio
    async def test_delete_files_with_errors(self, mock_hass, temp_dir):
        """Test: Löschen mit Fehlern."""
        # Erstelle eine existierende und eine nicht-existierende Datei
        existing_file = self.create_test_file(temp_dir, "exists.txt")
        non_existing_file = os.path.join(temp_dir, "nonexistent.txt")
        
        test_files = [existing_file, non_existing_file]
        
        # Mock async_add_executor_job für os.remove
        mock_hass.async_add_executor_job.return_value = None
        
        # Teste Löschung
        deleted_count, errors = await delete_files(mock_hass, test_files, dry_run=False)
        
        assert deleted_count == 1  # Nur die existierende Datei wurde gelöscht
        assert len(errors) == 1    # Ein Fehler beim Löschen der nicht-existierenden Datei
        
        # Prüfe, dass existierende Datei gelöscht wurde
        assert not os.path.exists(existing_file)
    
    @pytest.mark.asyncio
    async def test_analyze_file_ageing_case_insensitive_mask(self, mock_hass, temp_dir):
        """Test: Namensmaske ist case-insensitive."""
        # Erstelle Dateien mit verschiedenen Groß-/Kleinschreibungen
        self.create_test_file(temp_dir, "CONFIG.yaml", days_old=1)
        self.create_test_file(temp_dir, "config.YAML", days_old=2)
        self.create_test_file(temp_dir, "Config.yaml", days_old=3)
        
        # Mock os.listdir und os.stat
        mock_hass.async_add_executor_job.side_effect = [
            ["CONFIG.yaml", "config.YAML", "Config.yaml"],
            Mock(st_mtime=(datetime.now() - timedelta(days=1)).timestamp()),
            Mock(st_mtime=(datetime.now() - timedelta(days=2)).timestamp()),
            Mock(st_mtime=(datetime.now() - timedelta(days=3)).timestamp()),
        ]
        
        # Teste mit case-insensitive Maske "config"
        result = await analyze_file_ageing(mock_hass, temp_dir, "config")
        
        assert len(result) == 3  # Alle drei Dateien sollten gefunden werden
    
    @pytest.mark.asyncio
    async def test_analyze_file_ageing_empty_mask(self, mock_hass, temp_dir):
        """Test: Leere Namensmaske findet alle Dateien."""
        # Erstelle verschiedene Test-Dateien
        self.create_test_file(temp_dir, "file1.txt", days_old=1)
        self.create_test_file(temp_dir, "file2.log", days_old=2)
        self.create_test_file(temp_dir, "file3.yaml", days_old=3)
        
        # Mock os.listdir und os.stat
        mock_hass.async_add_executor_job.side_effect = [
            ["file1.txt", "file2.log", "file3.yaml"],  # os.listdir
            Mock(st_mtime=(datetime.now() - timedelta(days=1)).timestamp()),  # file1.txt
            Mock(st_mtime=(datetime.now() - timedelta(days=2)).timestamp()),  # file2.log
            Mock(st_mtime=(datetime.now() - timedelta(days=3)).timestamp()),  # file3.yaml
        ]
        
        # Teste mit leerer Maske
        result = await analyze_file_ageing(mock_hass, temp_dir, "")
        
        assert len(result) == 3  # Alle Dateien sollten gefunden werden


if __name__ == "__main__":
    pytest.main([__file__])
