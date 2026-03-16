#!/usr/bin/env python3
"""
Extract selective XML from srcML diff files.
Focuses on only the changed sections with minimal parent context.
Creates compact, semantically meaningful XML excerpts.
"""

import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import List, Tuple, Optional

class SelectiveXMLExtractor:
    """Extract relevant XML sections from srcML diff files."""
    
    def __init__(self):
        self.namespaces = {
            'diff': 'http://www.srcML.org/srcDiff',
            '': 'http://www.srcML.org/srcML/src'
        }
        # Register namespaces
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix if prefix else 'src', uri)
    
    def extract_selective_xml(self, xml_path: str, max_lines: int = 150) -> str:
        """
        Extract selective XML from a srcML diff file.
        
        Args:
            xml_path: Path to XML file
            max_lines: Maximum lines to return
            
        Returns:
            Compact XML excerpt focusing on changes
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Find all elements with diff changes
            changed_elements = self._find_changed_elements(root)
            
            if not changed_elements:
                return self._extract_fallback(xml_path)
            
            # Build excerpt with context
            excerpt = self._build_excerpt(changed_elements, root)
            
            # Limit output
            lines = excerpt.split('\n')
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                lines.append('... (truncated)')
            
            return '\n'.join(lines)
            
        except Exception as e:
            print(f"Error extracting XML from {xml_path}: {e}")
            return self._extract_fallback(xml_path)
    
    def _find_changed_elements(self, root) -> List:
        """Find all elements containing diff changes."""
        changed = []
        
        # Find all diff:insert and diff:delete elements
        for elem in root.iter():
            tag = elem.tag
            # Check if tag has diff namespace
            if '}insert' in tag or '}delete' in tag:
                # Find parent function/type if it exists
                parent = self._get_semantic_parent(root, elem)
                if parent is not None:
                    changed.append((parent, elem))
                else:
                    changed.append((elem, elem))
        
        return changed
    
    def _get_semantic_parent(self, root, elem):
        """Get the semantic parent (function, struct, class, etc.)."""
        # Find path from root to elem
        parent_map = {c: p for p in root.iter() for c in p}
        
        current = elem
        while current in parent_map:
            current = parent_map[current]
            tag = current.tag
            
            # Look for semantic containers
            if any(x in tag for x in ['function', 'struct', 'class', 'union']):
                return current
        
        return None
    
    def _build_excerpt(self, changed_elements: List, root) -> str:
        """Build compact XML excerpt from changed elements."""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<selective_xml_excerpt>',
            '  <changes>'
        ]
        
        added_parents = set()
        
        for parent, change in changed_elements:
            parent_id = id(parent)
            
            # Add parent if not already added
            if parent_id not in added_parents:
                parent_str = self._elem_to_compact_string(parent, max_depth=2)
                if parent_str:
                    lines.extend([f"  {line}" for line in parent_str.split('\n')])
                    added_parents.add(parent_id)
        
        lines.extend([
            '  </changes>',
            '</selective_xml_excerpt>'
        ])
        
        return '\n'.join(lines)
    
    def _elem_to_compact_string(self, elem, max_depth: int = 2, current_depth: int = 0) -> str:
        """Convert element to compact string representation."""
        if current_depth >= max_depth:
            return ''
        
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        attrs = ' '.join(f'{k}="{v}"' for k, v in elem.attrib.items())
        attr_str = f' {attrs}' if attrs else ''
        
        # Get text content
        text = (elem.text or '').strip()
        text_str = f'>{text}</elem>' if text else '/>'
        
        # Build opening tag
        result = f'<{tag}{attr_str}{text_str}\n' if '}' not in elem.tag or max_depth > 1 else f'<{tag}{attr_str}/>\n'
        
        # Add children with diff tags
        for child in elem:
            if 'diff' in child.tag:
                child_str = self._elem_to_compact_string(child, max_depth, current_depth + 1)
                if child_str:
                    result += child_str
        
        return result
    
    def _extract_fallback(self, xml_path: str) -> str:
        """Fallback extraction if structured parsing fails."""
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract sections with diff tags
            diff_sections = re.findall(r'<diff:\w+[^>]*>[\s\S]*?</diff:\w+>', content)
            
            if diff_sections:
                excerpt = '\n'.join(diff_sections[:20])  # Max 20 sections
                return f"<!-- Selective XML Excerpt -->\n{excerpt}"
            else:
                # Return first 100 lines as fallback
                lines = content.split('\n')[:100]
                return '\n'.join(lines)
                
        except Exception as e:
            return f"<!-- Error extracting XML: {e} -->"


def extract_xml_for_commit(commit_id: str, xml_files: List[dict]) -> str:
    """
    Extract selective XML for a specific commit.
    
    Args:
        commit_id: Commit ID
        xml_files: List of XML file info dicts with 'xml_path' keys
        
    Returns:
        Combined selective XML from all files for this commit
    """
    extractor = SelectiveXMLExtractor()
    excerpts = []
    
    for file_info in xml_files:
        xml_path = file_info.get('xml_path')
        if xml_path and Path(xml_path).exists():
            excerpt = extractor.extract_selective_xml(xml_path)
            if excerpt:
                file_name = file_info.get('file_name', 'unknown')
                excerpts.append(f"\n=== {file_name} ===\n{excerpt}")
    
    return '\n'.join(excerpts) if excerpts else "<!-- No selective XML available -->"


if __name__ == '__main__':
    # Test
    import json
    
    with open('processed_dataset.json') as f:
        dataset = json.load(f)
    
    for entry in dataset[:2]:
        xml_files = entry.get('xml_files', [])
        result = extract_xml_for_commit(entry['commit_id'], xml_files)
        print(f"\n{'='*60}")
        print(f"Commit: {entry['commit_id']}")
        print(f"Message: {entry['commit_message']}")
        print(f"Selective XML Length: {len(result)} chars")
        print(result[:500] + "...")
