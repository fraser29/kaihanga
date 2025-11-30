"""Example using SCAD and solidpython2 to build personalised napkin ring


"""
import argparse
import subprocess
from solid2 import (
    cylinder,
    difference,
    text,
    linear_extrude,
    translate,
    rotate,
    minkowski,
    sphere,
    scad_render_to_file,
)


def make_ring(outer_d, inner_d, height, name, chamfer_size=1.0):
    # Main ring body (outer cylinder minus inner cylinder)
    # Use minkowski with a small sphere to chamfer/round the edges
    ring_outer = cylinder(d=outer_d - chamfer_size * 2, h=height - chamfer_size * 2, _fn=100)
    ring_inner = cylinder(d=inner_d + chamfer_size * 2, h=height + 2, _fn=100)
    
    # Apply chamfer using minkowski with a sphere
    chamfer_sphere = sphere(r=chamfer_size, _fn=32)
    ring_outer_chamfered = minkowski()(ring_outer, chamfer_sphere)
    ring = difference()(ring_outer_chamfered, ring_inner)

    # Text: using a stencil font
    text_cut = linear_extrude(height=height * 5.0)(
        text(name,
             size=(outer_d - inner_d) * 1.2,    # auto text sizing
             font="Stardos Stencil",                    # Stardos Stencil, Gunplay, Know Your Product, Boston Traffic, Emblema One
             halign="center",
             valign="center")
    )

    # Position text so it cuts into outer surface
    # text_cut = translate([0, -(outer_d / 2) + 5, height/2])(rotate([90,0,0])(text_cut))
    text_cut = translate([0, 0, height/2])(rotate([90,0,0])(text_cut))


    # Subtract text from ring
    model = difference()(ring, text_cut)
    return model


def save_scad_and_stl(model, out_file):
    scad_file = out_file.replace(".stl", ".scad")

    # Write OpenSCAD file
    scad_render_to_file(model, scad_file)

    # Generate STL using OpenSCAD
    subprocess.run(
        ["openscad", "-o", out_file, scad_file],
        check=True
    )

    print(f"Generated: {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate a personalized napkin ring STL.")
    parser.add_argument("--outer", type=float, default=45, help="Outer diameter (mm) [default: 45]")
    parser.add_argument("--inner", type=float, default=38, help="Inner diameter (mm) [default: 38]")
    parser.add_argument("--height", type=float, default=25, help="Ring height (mm) [default: 25]")
    parser.add_argument("--name", type=str, required=True, help="Name to engrave")
    parser.add_argument("--out", type=str, default=None, help="Output STL filename [default: name_ring.stl]")

    args = parser.parse_args()

    model = make_ring(args.outer, args.inner, args.height, args.name)
    if args.out is None:
        args.out = f"{args.name}_ring.stl"
    save_scad_and_stl(model, args.out)


if __name__ == "__main__":
    main()
