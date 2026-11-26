"""Run inside Autodesk Fusion. Imports parameters only, not a T-Spline surface."""
import json
import math
from pathlib import Path

ALLOWED = {
    'sf_thickness': ('mm', .2, 15),
    'sf_padding': ('mm', 0, 20),
    'sf_clearance': ('mm', 0, 30),
    'sf_length': ('mm', 5, 2000),
    'sf_coverage': ('deg', 90, 270),
    'sf_seam_gap': ('mm', 0, 25),
    'sf_start_extension': ('mm', -100, 100),
    'sf_end_extension': ('mm', -100, 100),
}


def validated_rows(data):
    if not isinstance(data,dict) or data.get('schema')!='splintfit.fusion-parameters.v1' or data.get('units')!='mm':
        raise ValueError('Select fusion_user_parameters.json exported by SplintFit v3.')
    values=data.get('parameters')
    if not isinstance(values,list):raise ValueError('Missing parameters list.')
    rows=[];seen=set()
    for row in values:
        name=row.get('name') if isinstance(row,dict) else None
        if name not in ALLOWED or name in seen:raise ValueError('Unknown or duplicate parameter: '+str(name))
        unit,lo,hi=ALLOWED[name];value=row.get('value')
        if row.get('unit')!=unit or isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
            raise ValueError('Invalid value or unit for '+name)
        rows.append((name,unit,f'{value:.12g} {unit}'));seen.add(name)
    if seen!=set(ALLOWED):raise ValueError('Incomplete parameter set.')
    return rows


def apply_parameters(design,rows,make_value):
    # Validate dimensions and namespace conflicts before modifying the design.
    for name,unit,expression in rows:
        old=design.userParameters.itemByName(name)
        if old is None and design.allParameters.itemByName(name) is not None:
            raise ValueError('Name conflicts with a model parameter: '+name)
        if old is not None and not design.unitsManager.isValidExpression(expression,old.unit):
            raise ValueError('Existing parameter has an incompatible unit: '+name)
    updated=[];created=[]
    try:
        for name,unit,expression in rows:
            old=design.userParameters.itemByName(name)
            if old is None:
                item=design.userParameters.add(name,make_value(expression),unit,
                    'SplintFit research input; link explicitly to model features.')
                if item is None:raise RuntimeError('Could not add '+name)
                created.append(item)
            else:
                updated.append((old,old.expression));old.expression=expression
    except Exception:
        # Best-effort rollback. Fusion may still require Undo if model evaluation failed.
        for item,expression in reversed(updated):
            try:item.expression=expression
            except Exception:pass
        for item in reversed(created):
            try:item.deleteMe()
            except Exception:pass
        raise
    return len(created),len(updated)


def run(context):
    import adsk.core
    import adsk.fusion
    import traceback
    app=adsk.core.Application.get();ui=app.userInterface
    try:
        design=adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            ui.messageBox('Open a Fusion Design before running this script.');return
        dialog=ui.createFileDialog();dialog.title='Select SplintFit fusion_user_parameters.json'
        dialog.filter='JSON files (*.json)'
        if dialog.showOpen()!=adsk.core.DialogResults.DialogOK:return
        rows=validated_rows(json.loads(Path(dialog.filename).read_text(encoding='utf-8')))
        created,updated=apply_parameters(design,rows,adsk.core.ValueInput.createByString)
        ui.messageBox(f'Created {created}; updated {updated} user parameters.\n'
            'Link sf_thickness to an outward Thicken feature.\n'
            'OBJ already includes padding and clearance. Do not offset it twice.\n'
            'Changing these parameters does not automatically reshape the imported Form.')
    except Exception:
        ui.messageBox('Parameter import failed. Review/Undo the design if necessary.\n'+traceback.format_exc())
