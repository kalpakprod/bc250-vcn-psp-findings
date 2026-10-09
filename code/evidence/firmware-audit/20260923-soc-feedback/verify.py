import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'import/from-windows/Users/kukuruza/Downloads/AyuGram Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad'
b = SOURCE.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8'
nets = {}
current = None
for line in b.decode().splitlines():
    if line.startswith('SIGNAL '):
        current = line[7:]
        assert current not in nets
        nets[current] = []
    elif line.startswith('NODE ') and current is not None:
        _, ref, pin = line.split()
        nets[current].append([ref,pin])
expected = {
'SOC_FB': [('PCS9','2'),('PRS14','2'),('PRS15','1'),('PUS1','4')],
'SOC_FB_R': [('PRS11','2'),('PRS13','1'),('PRS14','1'),('PRS16','2')],
'N46990603': [('PCS9','1'),('PRS13','2')],
'N46990718': [('PRS12','2'),('PRS15','2'),('PRS17','2')],
'SOC_VSEN_LOC+': [('NSS1','2'),('PRS11','1')],
'SOC_VSEN_LOC-': [('NSS2','2'),('PRS12','1')],
'APU_VDDCR_SOC_RUN_FB_H': [('PRS16','1'),('R775','1'),('TP4','1'),('U25','BC20')],
'APU_VDDCR_SOC_RUN_FB_L': [('NS9','1'),('PRS17','1'),('R775','2')],
'SOC_VSS_SENSE2': [('NS10','2'),('NS11','2'),('NS9','2'),('TP18','1'),('U25','BD20')],
}
for net,nodes in expected.items():
    assert sorted(map(tuple,nets[net])) == sorted(nodes), net
assert ['NSS1','1'] in nets['+VDDCR_SOC']
assert ['NSS2','1'] in nets['GND']
result = {'status':'PASS','source':str(SOURCE),'sha256':hashlib.sha256(b).hexdigest(),
          'nets':{k:nets[k] for k in expected},
          'boundary_connections':{'NSS1.1':'+VDDCR_SOC','NSS2.1':'GND','U25.BC20':'APU_VDDCR_SOC_RUN_FB_H','U25.BD20':'SOC_VSS_SENSE2'},
          'finding':'No separately addressable DAC, digital potentiometer or switched transistor is listed on these exact feedback nets. RC/jumper/local sense and APU sense endpoints only.',
          'limits':['GenCAD revision NA, physical population not verified','APU internal pad behavior not proven','NS10/NS11 lead to other rail sense networks, not traced to their full circuits','No actual voltage or safe setpoint follows from this topology','Does not prove no indirect SoC control elsewhere']}
Path(__file__).with_name('result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS 9 complete feedback/sense nets and 2 local rail boundary connections')
