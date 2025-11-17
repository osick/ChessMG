"""
Tablebase Generator

High-level interface for generating tablebases.
Coordinates indexing, retrograde analysis, and storage.

Usage:
    generator = TablebaseGenerator()
    generator.generate_helpmate_tablebase(
        material=MaterialSignature.from_pieces([5, 0], [5]),  # KPvK
        output_dir=Path("./tablebases")
    )
"""

from typing import Optional, Callable
from pathlib import Path
import time

from .indexing import PositionIndexer, MaterialSignature
from .storage import TablebaseStorage, PositionValue
from .retrograde import RetrogradeAnalyzer


class TablebaseGenerator:
    """
    Generates tablebases for given material configurations.

    Provides progress tracking and handles the full generation pipeline.
    """

    def __init__(self):
        """Initialize tablebase generator."""
        self.current_material: Optional[MaterialSignature] = None
        self.current_indexer: Optional[PositionIndexer] = None
        self.current_analyzer: Optional[RetrogradeAnalyzer] = None

    def generate_helpmate_tablebase(
        self,
        material: MaterialSignature,
        output_dir: Path,
        max_depth: int = 7,
        use_symmetry: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> dict:
        """
        Generate a helpmate tablebase for a material configuration.

        Args:
            material: Material signature (e.g., KPvK)
            output_dir: Directory to save tablebase file
            max_depth: Maximum search depth in plies
            use_symmetry: Use symmetry reduction (experimental)
            progress_callback: Optional callback(phase, current, total)

        Returns:
            Statistics dictionary with generation results

        Example:
            >>> from pathlib import Path
            >>> from tablebase import MaterialSignature, TablebaseGenerator
            >>>
            >>> # Generate KvK tablebase
            >>> material = MaterialSignature.from_pieces([5], [5])
            >>> generator = TablebaseGenerator()
            >>> stats = generator.generate_helpmate_tablebase(
            ...     material=material,
            ...     output_dir=Path("./tablebases")
            ... )
            >>> print(f"Generated {stats['legal_positions']:,} positions")
        """
        self.current_material = material
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Output file
        output_file = output_dir / f"{material}.cmgtb"

        print(f"\n{'='*70}")
        print(f"Generating Helpmate Tablebase: {material}")
        print(f"{'='*70}")

        start_time = time.time()

        # Phase 1: Create indexer
        print(f"\n[1/4] Creating position indexer...")
        self.current_indexer = PositionIndexer(material, use_symmetry=use_symmetry)
        print(f"  Max positions: {self.current_indexer.max_index():,}")

        # Phase 2: Initialize storage
        print(f"\n[2/4] Initializing storage ({output_file.name})...")
        storage = TablebaseStorage(
            output_file,
            material,
            self.current_indexer.max_index(),
            mode='w'
        )
        data_size_mb = storage.data_size / (1024 * 1024)
        print(f"  Storage size: {data_size_mb:.2f} MB")

        # Phase 3: Run retrograde analysis
        print(f"\n[3/4] Running retrograde analysis (max depth: {max_depth})...")
        self.current_analyzer = RetrogradeAnalyzer(material, self.current_indexer)

        def analysis_progress(ply: int, positions_found: int):
            """Progress callback for retrograde analysis."""
            print(f"  Ply {ply}: Found {positions_found:,} new helpmate positions")
            if progress_callback:
                progress_callback("retrograde", ply, max_depth)

        stats = self.current_analyzer.generate_helpmate_tablebase(
            storage,
            max_depth=max_depth,
            progress_callback=analysis_progress
        )

        # Phase 4: Finalize
        print(f"\n[4/4] Finalizing...")
        storage.close()

        # Add timing info
        elapsed = time.time() - start_time
        stats['generation_time_seconds'] = elapsed

        # Print summary
        print(f"\n{'='*70}")
        print(f"Generation Complete!")
        print(f"{'='*70}")
        print(f"Material:          {material}")
        print(f"Output file:       {output_file}")
        print(f"Total positions:   {stats['total_positions']:,}")
        print(f"Legal positions:   {stats['legal_positions']:,}")
        print(f"  - Helpmate:      {stats['helpmate_positions']:,}")
        print(f"  - Draw:          {stats['draw_positions']:,}")
        print(f"Illegal positions: {stats['illegal_positions']:,}")
        print(f"Max DTM:           {stats['max_dtm']}")
        print(f"Generation time:   {elapsed:.2f}s")
        print(f"{'='*70}\n")

        return stats

    def generate_multiple(
        self,
        materials: list,
        output_dir: Path,
        **kwargs
    ) -> dict:
        """
        Generate multiple tablebases sequentially.

        Args:
            materials: List of MaterialSignature objects
            output_dir: Output directory
            **kwargs: Additional arguments passed to generate_helpmate_tablebase

        Returns:
            Dictionary mapping material -> stats
        """
        results = {}

        for i, material in enumerate(materials):
            print(f"\n\n{'#'*70}")
            print(f"# Generating tablebase {i+1}/{len(materials)}: {material}")
            print(f"{'#'*70}\n")

            stats = self.generate_helpmate_tablebase(
                material=material,
                output_dir=output_dir,
                **kwargs
            )
            results[str(material)] = stats

        return results

    def estimate_size(self, material: MaterialSignature) -> dict:
        """
        Estimate tablebase size without generating.

        Args:
            material: Material signature

        Returns:
            Dictionary with size estimates
        """
        indexer = PositionIndexer(material)
        max_positions = indexer.max_index()

        # 4 bits per position
        data_size_bytes = (max_positions + 1) // 2
        data_size_mb = data_size_bytes / (1024 * 1024)

        # Add header
        total_size_mb = data_size_mb + TablebaseStorage.HEADER_SIZE / (1024 * 1024)

        return {
            'material': str(material),
            'max_positions': max_positions,
            'data_size_mb': data_size_mb,
            'total_size_mb': total_size_mb,
        }

    def validate_tablebase(self, filepath: Path) -> dict:
        """
        Validate a generated tablebase file.

        Args:
            filepath: Path to tablebase file

        Returns:
            Validation results dictionary
        """
        print(f"Validating {filepath}...")

        # Try to open
        try:
            # Read header to get material
            with open(filepath, 'rb') as f:
                magic = f.read(5)
                if magic != TablebaseStorage.MAGIC:
                    return {'valid': False, 'error': 'Invalid magic number'}

                version = f.read(1)[0]
                if version != TablebaseStorage.VERSION:
                    return {'valid': False, 'error': f'Unsupported version: {version}'}

            # Get material from filename
            material_str = filepath.stem

            # Try to open storage
            # We need to parse material signature from string
            # For now, just check file integrity
            print(f"  File structure: OK")
            print(f"  Material: {material_str}")

            return {
                'valid': True,
                'material': material_str,
                'filepath': str(filepath),
                'size_mb': filepath.stat().st_size / (1024 * 1024)
            }

        except Exception as e:
            return {'valid': False, 'error': str(e)}
