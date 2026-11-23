"""Reproduce the synthetic example without opening the desktop UI."""
import argparse
from pathlib import Path
from cast_template import hand_demo_mesh
from geometry import Parameters,build,export_bundle


def main():
    cli=argparse.ArgumentParser(description='Create synthetic perforated two-piece cast (not patient data).')
    cli.add_argument('--output',default='my_demo_export',help='New output directory, must not already exist')
    args=cli.parse_args()
    mesh=hand_demo_mesh()
    p=Parameters(proximal_point=[34.,0.,15.],distal_point=[40.,0.,288.],side_point=[25.,0.,175.],
       splint_mode='bivalve',cast_template=True,hand_notch_depth_mm=35.,auto_orient_open_normals=True)
    result=build(mesh,p,lambda n,message:print(f'{n:3d}% {message}',flush=True))
    out=export_bundle(Path(args.output),mesh,result,p,{'synthetic_demo':True,'synthetic_demo_kind':'hand_envelope_v1'})
    print(f'Exported to {out.resolve()}')


if __name__=='__main__':main()
