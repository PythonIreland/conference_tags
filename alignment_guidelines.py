def draw_guidelines(layout):
    """Helps to see the proportions on the badge"""
    # horizontals
    layout.canvas.setDash(1, 8)
    # 1/4 and 1/8
    for proportion in [1 / 8, 1 / 4, 1 / 2, 3 / 4, 7 / 8]:
        layout.canvas.line(
            0,
            layout.margin + layout.section_height * proportion,
            layout.width,
            layout.margin + layout.section_height * proportion,
        )

    layout.canvas.setDash(2, 2)
    # 1/6, 1/3, 2/3 horizontal from the bottom
    for proportion in [1 / 6, 1 / 3, 2 / 3]:
        layout.canvas.line(
            0,
            layout.margin + layout.section_height * proportion,
            layout.width,
            layout.margin + layout.section_height * proportion,
        )

    # 1/3 for conf banner
    # 1/3 for logo
    # 1/3 for name and role (1/6 each)
    layout.canvas.setDash(1, 0)


def draw_margins(layout):
    """Margin materialisation"""
    if layout.margin:
        layout.canvas.setDash(1, 4)
        layout.canvas.line(
            layout.width / 2.0 - layout.margin,
            0,
            layout.width / 2.0 - layout.margin,
            layout.height,
        )
        layout.canvas.line(
            layout.width / 2.0 + layout.margin,
            0,
            layout.width / 2.0 + layout.margin,
            layout.height,
        )
        layout.canvas.line(
            0,
            layout.height / 2.0 + layout.margin,
            layout.width,
            layout.height / 2.0 + layout.margin,
        )
        layout.canvas.line(
            0,
            layout.height / 2.0 - layout.margin,
            layout.width,
            layout.height / 2.0 - layout.margin,
        )
        layout.canvas.setDash(1, 0)
