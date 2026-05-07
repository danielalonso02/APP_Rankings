"""
Logo Utilities
Handles team logo loading, processing, and base64 encoding for use across the application.
"""

import base64
import os
import io
import logging

from PIL import Image

from utils.constants import TEAM_LOGO_MAPPINGS

logger = logging.getLogger(__name__)


def _get_logo_path(team_name, logos_dir):
    """
    Resolve the file path for a team's logo.
    Returns the path if found, None otherwise.
    """
    logo_filename = TEAM_LOGO_MAPPINGS.get(team_name.strip())
    if not logo_filename:
        logger.warning("No mapping found for team: %s", team_name)
        return None

    logo_path = os.path.join(logos_dir, logo_filename)
    if not os.path.exists(logo_path):
        logger.warning("Logo file not found: %s", logo_path)
        return None

    return logo_path


def _load_image_rgba(logo_path):
    """Load an image and convert to RGBA mode."""
    img = Image.open(logo_path)
    if img.mode in ('P', 'L', 'RGB'):
        img = img.convert('RGBA')
    return img


def _image_to_base64(img):
    """Convert a PIL Image to a base64-encoded data URI string."""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def get_team_logo_base64_square(team_name, logos_dir, size=50):
    """
    Get base64 encoded team logo fitted into a square canvas while maintaining aspect ratio.
    All logos will be the same dimensions (size x size) with transparent padding.

    Parameters:
    - team_name: Name of the team
    - logos_dir: Directory containing logo files
    - size: Square dimension in pixels (default 50)

    Returns:
    - Base64 encoded image string in format "data:image/png;base64,..." or None if not found
    """
    logo_path = _get_logo_path(team_name, logos_dir)
    if not logo_path:
        return None

    try:
        img = _load_image_rgba(logo_path)

        original_width, original_height = img.size
        aspect_ratio = original_width / original_height

        if aspect_ratio > 1:
            new_width = size
            new_height = int(size / aspect_ratio)
        else:
            new_height = size
            new_width = int(size * aspect_ratio)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        x_offset = (size - new_width) // 2
        y_offset = (size - new_height) // 2
        canvas.paste(img, (x_offset, y_offset), img)

        return _image_to_base64(canvas)

    except Exception as e:
        logger.error("Error loading logo for %s: %s", team_name, e)
        return None


def get_team_logo_base64(team_name, logos_dir, width=50, height=50, maintain_aspect_ratio=True):
    """
    Get base64 encoded team logo with proper sizing and aspect ratio control.

    Parameters:
    - team_name: Name of the team
    - logos_dir: Directory containing logo files
    - width: Target width in pixels (default 50)
    - height: Target height in pixels (default 50)
    - maintain_aspect_ratio: If True, fit within width/height while maintaining original aspect ratio
                            If False, stretch to exact width/height (default True)

    Returns:
    - Base64 encoded image string in format "data:image/png;base64,..." or None if not found
    """
    logo_path = _get_logo_path(team_name, logos_dir)
    if not logo_path:
        return None

    try:
        img = _load_image_rgba(logo_path)

        if maintain_aspect_ratio:
            original_width, original_height = img.size
            aspect_ratio = original_width / original_height

            if aspect_ratio > (width / height):
                new_width = width
                new_height = int(width / aspect_ratio)
            else:
                new_height = height
                new_width = int(height * aspect_ratio)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((width, height), Image.Resampling.LANCZOS)

        return _image_to_base64(img)

    except Exception as e:
        logger.error("Error loading logo for %s: %s", team_name, e)
        return None


def get_team_logo_path(team_name, logos_dir):
    """
    Get the file path for a team's logo.

    Parameters:
    - team_name: Name of the team
    - logos_dir: Directory containing logo files

    Returns:
    - Full path to logo file or None if not found
    """
    return _get_logo_path(team_name, logos_dir)


def create_scatter_with_logos_plotly(df, x_col, y_col, team_col, logos_dir,
                                      title, xlabel, ylabel, logo_size=50,
                                      figure_width=1000, figure_height=700,
                                      logo_visual_percent=0.045):
    """
    Create interactive Plotly scatter plot with team logos.
    All logos will be displayed at uniform VISUAL size across all plots.

    Parameters:
    - df: DataFrame with data
    - x_col, y_col: Column names for x and y axes
    - team_col: Column name for team names
    - logos_dir: Directory containing logo files
    - title, xlabel, ylabel: Plot labels
    - logo_size: Size for logo pixels (default 50) - used for base64 image generation
    - figure_width: Figure width in pixels (default 1000)
    - figure_height: Figure height in pixels (default 700)
    - logo_visual_percent: Percentage of figure dimension for logo size (default 0.045 = 4.5%)

    Returns:
    - Plotly figure
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='markers',
        marker=dict(
            size=logo_size,
            color='rgba(0,0,0,0)',
            line=dict(width=0)
        ),
        text=df[team_col],
        hovertemplate='<b>%{text}</b><br>' +
                      f'{ylabel}: %{{y:.2f}}<br>' +
                      f'{xlabel}: %{{x:.2f}}<br>' +
                      '<extra></extra>',
        showlegend=False
    ))

    x_range = df[x_col].max() - df[x_col].min()
    y_range = df[y_col].max() - df[y_col].min()

    x_padding = x_range * 0.1
    y_padding = y_range * 0.1

    logo_size_x_data = x_range * logo_visual_percent * (figure_height / figure_width)
    logo_size_y_data = y_range * logo_visual_percent
    logo_size_data = min(logo_size_x_data, logo_size_y_data) * 1.2

    teams_plotted = 0
    teams_failed = []

    for _, row in df.iterrows():
        team = row[team_col]
        x_val = row[x_col]
        y_val = row[y_col]

        logo_base64 = get_team_logo_base64_square(team, logos_dir, size=logo_size)

        if logo_base64:
            fig.add_layout_image(
                dict(
                    source=logo_base64,
                    xref="x",
                    yref="y",
                    x=x_val,
                    y=y_val,
                    sizex=logo_size_data,
                    sizey=logo_size_data,
                    xanchor="center",
                    yanchor="middle",
                    layer="above"
                )
            )
            teams_plotted += 1
        else:
            teams_failed.append(team)

    logger.info("Teams plotted: %d/%d", teams_plotted, len(df))
    if teams_failed:
        logger.warning("Failed to plot logos for: %s", teams_failed)

    min_val = min(df[x_col].min(), df[y_col].min())
    max_val = max(df[x_col].max(), df[y_col].max())

    fig.add_shape(
        type="line",
        x0=min_val, y0=min_val,
        x1=max_val, y1=max_val,
        line=dict(color="gray", dash="dash", width=2),
        layer="below"
    )

    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#1e293b')),
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        template="plotly_white",
        height=figure_height,
        width=figure_width,
        hovermode="closest",
        xaxis=dict(
            range=[df[x_col].min() - x_padding, df[x_col].max() + x_padding],
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            range=[df[y_col].min() - y_padding, df[y_col].max() + y_padding],
            gridcolor='#e5e7eb'
        ),
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color='#1e293b')
    )

    return fig
