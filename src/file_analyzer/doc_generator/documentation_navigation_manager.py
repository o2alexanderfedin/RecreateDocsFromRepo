"""
Documentation navigation manager for creating navigation elements.

This module enhances documentation with navigation elements including
table of contents, breadcrumbs, cross-references, and section navigation.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

import jinja2
from file_analyzer.doc_generator.markdown_formatter import (
    sanitize_markdown,
    create_anchor_link
)

logger = logging.getLogger("file_analyzer.doc_generator")


class NavigationConfig:
    """Configuration for documentation navigation."""
    
    def __init__(
        self,
        output_dir: str,
        template_dir: Optional[str] = None,
        include_breadcrumbs: bool = True,
        include_toc: bool = True,
        include_section_nav: bool = True,
        include_cross_references: bool = True,
        include_footer_nav: bool = True,
        max_toc_depth: int = 3,
        max_breadcrumb_segments: int = 5,
        navigation_templates_dir: Optional[str] = None
    ):
        """
        Initialize navigation configuration.
        
        Args:
            output_dir: Directory where documentation is generated
            template_dir: Custom template directory (optional)
            include_breadcrumbs: Whether to include breadcrumb navigation
            include_toc: Whether to include table of contents
            include_section_nav: Whether to include section navigation
            include_cross_references: Whether to include cross-references
            include_footer_nav: Whether to include footer navigation
            max_toc_depth: Maximum depth for table of contents
            max_breadcrumb_segments: Maximum segments in breadcrumb trail
            navigation_templates_dir: Custom templates for navigation elements
        """
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.include_breadcrumbs = include_breadcrumbs
        self.include_toc = include_toc
        self.include_section_nav = include_section_nav
        self.include_cross_references = include_cross_references
        self.include_footer_nav = include_footer_nav
        self.max_toc_depth = max_toc_depth
        self.max_breadcrumb_segments = max_breadcrumb_segments
        self.navigation_templates_dir = navigation_templates_dir


class DocumentationNavigationManager:
    """
    Manages navigation elements within documentation.
    
    This class enhances documentation with navigation elements such as
    table of contents, breadcrumbs, cross-references, and section navigation
    to improve user experience and make the documentation more navigable.
    """
    
    def __init__(self, config: NavigationConfig):
        """
        Initialize the documentation navigation manager.
        
        Args:
            config: Navigation configuration
        """
        self.config = config
        
        # Set up Jinja2 environment
        template_dirs = []
        
        # Add custom navigation templates directory if provided
        if config.navigation_templates_dir:
            template_dirs.append(config.navigation_templates_dir)
        
        # Add custom template directory if provided
        if config.template_dir:
            template_dirs.append(config.template_dir)
        
        # Add default template directory
        default_template_dir = os.path.join(
            os.path.dirname(__file__), "templates"
        )
        template_dirs.append(default_template_dir)
        
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dirs),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.jinja_env.filters['basename'] = lambda path: os.path.basename(path)
        self.jinja_env.filters['sanitize_markdown'] = sanitize_markdown
        self.jinja_env.filters['create_anchor'] = create_anchor_link
    
    def generate_toc(self, document: Dict[str, Any]) -> str:
        """
        Generate table of contents for a document.
        
        Args:
            document: Document metadata including headings
            
        Returns:
            Markdown string with table of contents
        """
        toc_lines = ["## Table of Contents\n"]
        
        # Extract headings from document
        headings = document.get("headings", [])
        
        # Skip the title (first h1)
        start_index = 0
        for i, heading in enumerate(headings):
            if heading.get("level") == 1:
                start_index = i + 1
                break
        
        # Generate TOC entries for remaining headings
        for heading in headings[start_index:]:
            level = heading.get("level", 2)
            
            # Skip headings deeper than max_toc_depth
            if level > self.config.max_toc_depth + 1:
                continue
                
            text = heading.get("text", "")
            indent = "  " * (level - 2)  # Indent based on heading level
            anchor = create_anchor_link(text)
            
            toc_lines.append(f"{indent}- [{text}](#{anchor})")
        
        return "\n".join(toc_lines)
    
    def generate_breadcrumbs(
        self,
        document: Dict[str, Any],
        doc_structure: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate breadcrumb navigation for a document.
        
        Args:
            document: Document metadata
            doc_structure: Complete documentation structure
            
        Returns:
            Markdown string with breadcrumb navigation
        """
        breadcrumbs = []
        current_path = document.get("path", "")
        
        # Build breadcrumb chain by following parent links
        while current_path:
            current_doc = doc_structure.get(current_path)
            if not current_doc:
                break
                
            # Add current document to breadcrumbs
            title = current_doc.get("title", os.path.basename(current_path))
            breadcrumbs.insert(0, (title, current_path))
            
            # Move to parent
            current_path = current_doc.get("parent", "")
            
            # Prevent infinite loops
            if len(breadcrumbs) >= 20:  # Safeguard against circular references
                break
        
        # Truncate if too long
        if len(breadcrumbs) > self.config.max_breadcrumb_segments:
            # Keep first, last, and middle elements
            visible_count = self.config.max_breadcrumb_segments
            breadcrumbs = (
                breadcrumbs[:max(1, visible_count // 2)] + 
                [("...", "")] + 
                breadcrumbs[-max(1, visible_count // 2):]
            )
        
        # Format breadcrumbs as Markdown
        breadcrumb_links = []
        for i, (title, path) in enumerate(breadcrumbs):
            # Skip empty segments or placeholders
            if not title or title == "...":
                breadcrumb_links.append("...")
                continue
                
            # For the current page (last item), don't make it a link
            if i == len(breadcrumbs) - 1:
                breadcrumb_links.append(title)
                continue
            
            # Calculate relative path
            current_doc_path = document.get("path", "")
            relative_path = self._get_relative_path(current_doc_path, path)
            
            # Add as link
            breadcrumb_links.append(f"[{title}]({relative_path})")
        
        # Join with separator
        return " &raquo; ".join(breadcrumb_links)
    
    def generate_section_navigation(self, document: Dict[str, Any]) -> str:
        """
        Generate section navigation for a document.
        
        Args:
            document: Document metadata including headings
            
        Returns:
            Markdown string with section navigation
        """
        # Extract headings from document
        headings = document.get("headings", [])
        
        # Skip the title (first h1)
        start_index = 0
        for i, heading in enumerate(headings):
            if heading.get("level") == 1:
                start_index = i + 1
                break
        
        # Use only h2 headings for section navigation
        section_headings = []
        for heading in headings[start_index:]:
            if heading.get("level") == 2:
                section_headings.append(heading)
        
        # If not enough sections, return empty navigation
        if len(section_headings) < 2:
            return ""
        
        # Create section navigation links
        nav_links = []
        for heading in section_headings:
            text = heading.get("text", "")
            anchor = create_anchor_link(text)
            nav_links.append(f"[{text}](#{anchor})")
        
        return "Section Navigation: " + " | ".join(nav_links)
    
    def generate_cross_references(
        self,
        document: Dict[str, Any],
        doc_structure: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate cross-references to related documents.
        
        Args:
            document: Document metadata
            doc_structure: Complete documentation structure
            
        Returns:
            Markdown string with cross-references
        """
        related_files = document.get("related_files", [])
        
        # If no related files, return empty string
        if not related_files:
            return ""
        
        # Build cross-references section
        xref_lines = ["## Related Files\n"]
        
        current_path = document.get("path", "")
        current_dir = os.path.dirname(current_path)
        
        for related_path in related_files:
            related_doc = doc_structure.get(related_path)
            if not related_doc:
                continue
                
            # Get title or fallback to filename
            title = related_doc.get("title", os.path.basename(related_path))
            
            # Calculate relative path
            relative_path = self._get_relative_path(current_path, related_path)
            
            # Add to cross-references
            xref_lines.append(f"- [{title}]({relative_path})")
        
        return "\n".join(xref_lines)
    
    def generate_header_footer(
        self,
        document: Dict[str, Any],
        doc_structure: Dict[str, Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Generate header and footer navigation elements.
        
        Args:
            document: Document metadata
            doc_structure: Complete documentation structure
            
        Returns:
            Tuple of (header, footer) Markdown strings
        """
        # Generate header with basic navigation
        header_lines = []
        
        # Add breadcrumbs if enabled
        if self.config.include_breadcrumbs:
            breadcrumbs = self.generate_breadcrumbs(document, doc_structure)
            if breadcrumbs:
                header_lines.append(breadcrumbs)
                header_lines.append("")  # Add blank line after breadcrumbs
        
        # Generate footer with navigation links
        footer_lines = []
        
        if self.config.include_footer_nav:
            footer_lines.append("---\n")
            footer_lines.append("## Navigation\n")
            
            # Add link to home page
            current_path = document.get("path", "")
            home_path = self._get_relative_path(current_path, "index.md")
            footer_lines.append(f"- [Home]({home_path})")
            
            # Add link to parent directory if available
            parent_path = document.get("parent", "")
            if parent_path:
                parent_title = doc_structure.get(parent_path, {}).get("title", "Parent Directory")
                parent_rel_path = self._get_relative_path(current_path, parent_path)
                footer_lines.append(f"- [Up to {parent_title}]({parent_rel_path})")
            
            # If this is not an index page, add link to directory index
            if not current_path.endswith("index.md"):
                dir_path = os.path.dirname(current_path)
                dir_index = f"{dir_path}/index.md" if dir_path else "index.md"
                if dir_index in doc_structure:
                    dir_title = doc_structure.get(dir_index, {}).get("title", "Directory Index")
                    dir_rel_path = self._get_relative_path(current_path, dir_index)
                    footer_lines.append(f"- [Directory: {dir_title}]({dir_rel_path})")
        
        # Return header and footer
        return "\n".join(header_lines), "\n".join(footer_lines)
    
    def add_navigation_to_document(
        self,
        content: str,
        document: Dict[str, Any],
        doc_structure: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Add navigation elements to a document.
        
        Args:
            content: Original document content
            document: Document metadata
            doc_structure: Complete documentation structure
            
        Returns:
            Document content with navigation elements
        """
        # Split content into parts - we'll insert navigation at appropriate points
        # First, ensure we have a title
        title_match = re.match(r'^# (.+)$', content, re.MULTILINE)
        if not title_match:
            # If no title, add document title from metadata
            title = document.get("title", os.path.basename(document.get("path", "")))
            content = f"# {title}\n\n{content}"
        
        # Find where to insert navigation - after the title
        parts = re.split(r'^# .+$', content, 1, re.MULTILINE)
        if len(parts) != 2:
            # Fallback to beginning if can't find title
            header_part = ""
            body_part = content
        else:
            header_part = parts[0] + re.search(r'^# .+$', content, re.MULTILINE).group(0)
            body_part = parts[1]
        
        # Generate navigation elements
        navigation_elements = []
        
        # Add header navigation
        if self.config.include_breadcrumbs:
            header, _ = self.generate_header_footer(document, doc_structure)
            if header:
                navigation_elements.append(header)
        
        # Add table of contents
        if self.config.include_toc:
            toc = self.generate_toc(document)
            if toc:
                navigation_elements.append(toc)
        
        # Add section navigation
        if self.config.include_section_nav:
            section_nav = self.generate_section_navigation(document)
            if section_nav:
                navigation_elements.append(section_nav)
        
        # Add cross-references - these go at the end
        cross_references = ""
        if self.config.include_cross_references:
            cross_references = self.generate_cross_references(document, doc_structure)
        
        # Add footer navigation
        footer = ""
        if self.config.include_footer_nav:
            _, footer = self.generate_header_footer(document, doc_structure)
        
        # Combine everything
        result = header_part + "\n"
        if navigation_elements:
            result += "\n".join(navigation_elements) + "\n\n"
        result += body_part
        
        # Add cross-references and footer at the end
        if cross_references:
            result += "\n\n" + cross_references
        
        if footer:
            result += "\n\n" + footer
        
        return result
    
    def process_documentation_structure(
        self,
        document_files: List[Dict[str, Any]],
        doc_structure: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a complete documentation structure to add navigation.
        
        Args:
            document_files: List of document files with metadata
            doc_structure: Complete documentation structure
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "total_files": len(document_files),
            "processed_files": 0,
            "skipped_files": 0
        }
        
        for doc_file in document_files:
            file_path = doc_file.get("file_path", "")
            metadata = doc_file.get("metadata", {})
            
            # Skip files that don't exist
            if not os.path.exists(file_path):
                stats["skipped_files"] += 1
                continue
            
            try:
                # Read the file content
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Add navigation elements
                updated_content = self.add_navigation_to_document(
                    content, metadata, doc_structure
                )
                
                # Write the updated content back
                with open(file_path, "w") as f:
                    f.write(updated_content)
                
                stats["processed_files"] += 1
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                stats["skipped_files"] += 1
        
        return stats
    
    def _get_relative_path(self, from_path: str, to_path: str) -> str:
        """
        Calculate relative path between documentation files.
        
        Args:
            from_path: Source document path
            to_path: Target document path
            
        Returns:
            Relative path from source to target
        """
        # Convert paths to Path objects
        from_path_obj = Path(from_path)
        to_path_obj = Path(to_path)
        
        # Get directory of source file
        from_dir = from_path_obj.parent
        
        # Calculate relative path
        try:
            rel_path = os.path.relpath(to_path_obj, from_dir)
            # Ensure proper path separator
            rel_path = rel_path.replace("\\", "/")
            return rel_path
        except ValueError:
            # Fallback to absolute path for unrelated paths
            return "/" + str(to_path_obj).replace("\\", "/")
    
    def extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract headings from a Markdown document.
        
        Args:
            content: Markdown content
            
        Returns:
            List of headings with level and text
        """
        headings = []
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        
        for line in content.split('\n'):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    "level": level,
                    "text": text
                })
        
        return headings
    
    def build_doc_structure(self, documentation_files: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Build a comprehensive documentation structure from files.
        
        Args:
            documentation_files: List of documentation file paths
            
        Returns:
            Dictionary with document structure metadata
        """
        doc_structure = {}
        
        # First pass: Extract basic metadata from each file
        for file_path in documentation_files:
            try:
                # Read file content
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Convert absolute path to relative path for structure keys
                rel_path = os.path.relpath(
                    file_path, 
                    self.config.output_dir
                ).replace("\\", "/")
                
                # Extract title from first heading
                title = os.path.basename(file_path)
                heading_match = re.search(r'^# (.+)$', content, re.MULTILINE)
                if heading_match:
                    title = heading_match.group(1).strip()
                
                # Extract all headings
                headings = self.extract_headings(content)
                
                # Store metadata
                doc_structure[rel_path] = {
                    "title": title,
                    "path": rel_path,
                    "headings": headings,
                    "children": [],
                    "parent": ""
                }
            except Exception as e:
                logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
        
        # Second pass: Build parent-child relationships
        for rel_path, metadata in doc_structure.items():
            dir_name = os.path.dirname(rel_path)
            
            # Skip if this is a root file
            if not dir_name:
                continue
            
            # Check for parent index file
            parent_index = f"{dir_name}/index.md" if dir_name else "index.md"
            if parent_index in doc_structure:
                # Set parent
                metadata["parent"] = parent_index
                
                # Add to parent's children
                doc_structure[parent_index]["children"].append(rel_path)
            else:
                # Try to find closest parent by traversing up
                parent_found = False
                current_dir = dir_name
                
                while current_dir:
                    parent_candidate = f"{current_dir}/index.md"
                    if parent_candidate in doc_structure:
                        metadata["parent"] = parent_candidate
                        doc_structure[parent_candidate]["children"].append(rel_path)
                        parent_found = True
                        break
                    
                    # Move up one directory
                    current_dir = os.path.dirname(current_dir)
                
                # If no parent found, link to root index
                if not parent_found and "index.md" in doc_structure:
                    metadata["parent"] = "index.md"
                    doc_structure["index.md"]["children"].append(rel_path)
        
        # Third pass: Build related files based on content references
        for rel_path, metadata in doc_structure.items():
            try:
                file_path = os.path.join(self.config.output_dir, rel_path)
                
                # Read file content
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Find Markdown links to other documentation files
                link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                link_matches = re.findall(link_pattern, content)
                
                related_files = set()
                for link_text, link_target in link_matches:
                    # Normalize link target
                    if link_target.startswith("#"):
                        # Skip internal links
                        continue
                        
                    # Convert relative link to absolute path
                    target_dir = os.path.dirname(rel_path)
                    target_path = os.path.normpath(
                        os.path.join(target_dir, link_target)
                    ).replace("\\", "/")
                    
                    # If this links to a documentation file, add it as related
                    if target_path in doc_structure:
                        related_files.add(target_path)
                
                # Store related files
                metadata["related_files"] = list(related_files)
                
            except Exception as e:
                logger.error(f"Error finding related files for {rel_path}: {str(e)}")
        
        return doc_structure