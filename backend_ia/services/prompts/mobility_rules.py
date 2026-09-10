def get_mobility_prompt() -> str:
    """Mobility, traffic and route planning rules."""
    return (
        "### MOBILITY & ROUTES DOMAIN:\n"
        "- When user says 'casa' (home), use configured home address as reference point.\n"
        "- For any other destination in free text, query routes and traffic directly by the location name provided.\n"
    )
