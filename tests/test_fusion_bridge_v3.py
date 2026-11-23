import importlib.util,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fusion_import',root/'fusion/SplintFitImport/SplintFitImport.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
from geometry import Parameters,demo_mesh,build,export_bundle
import json


class FusionBridgeTests(unittest.TestCase):
    def test_exported_parameters_have_explicit_mm_and_degrees(self):
        p=Parameters(thickness_mm=4.2);mesh=demo_mesh()
        with tempfile.TemporaryDirectory() as temp:
            output=export_bundle(Path(temp)/'out',mesh,build(mesh,p),p,{})
            rows=bridge.validated_rows(json.loads((output/'fusion_user_parameters.json').read_text()))
            values={name:(unit,expression) for name,unit,expression in rows}
            self.assertEqual(values['sf_thickness'],('mm','4.2 mm'))
            self.assertEqual(values['sf_coverage'],('deg','180 deg'))
            self.assertTrue((output/'fusion/SplintFitImport/SplintFitImport.manifest').is_file())

    def test_import_rejects_expressions_duplicate_names_and_bad_units(self):
        base={'schema':'splintfit.fusion-parameters.v1','units':'mm',
            'parameters':[{'name':name,'unit':unit,'value':max(1,lo)} for name,(unit,lo,hi) in bridge.ALLOWED.items()]}
        for change in ('expression','unit','duplicate'):
            data=json.loads(json.dumps(base))
            if change=='expression':data['parameters'][0]['value']='3 mm + 100'
            if change=='unit':data['parameters'][0]['unit']='cm'
            if change=='duplicate':data['parameters'].append(data['parameters'][0])
            with self.subTest(change=change),self.assertRaises(ValueError):bridge.validated_rows(data)

    def test_update_failure_restores_previously_changed_parameter(self):
        from types import SimpleNamespace
        class Item:
            def __init__(self,value,fail=False):self._value=value;self.fail=fail;self.unit='mm'
            @property
            def expression(self):return self._value
            @expression.setter
            def expression(self,value):
                if self.fail:raise RuntimeError('Fusion evaluation failure')
                self._value=value
        first,second=Item('2 mm'),Item('3 mm',fail=True)
        parameters={'sf_thickness':first,'sf_padding':second}
        collection=SimpleNamespace(itemByName=parameters.get)
        design=SimpleNamespace(userParameters=collection,allParameters=collection,
            unitsManager=SimpleNamespace(isValidExpression=lambda expr,unit:True))
        with self.assertRaises(RuntimeError):
            bridge.apply_parameters(design,[('sf_thickness','mm','4 mm'),('sf_padding','mm','5 mm')],str)
        self.assertEqual(first.expression,'2 mm')
