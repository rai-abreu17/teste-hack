"""Analyze an existing binary frame without any simulator/evaluation dependency."""
import argparse
import json
from pathlib import Path
from .estimators import estimate_tin,estimate_parametric
from .measured_zero import MeasuredZero,estimate_with_zero


def main():
    parser = argparse.ArgumentParser(description='Análise experimental de um quadro binário BoxFlow simulado')
    parser.add_argument('frame',type=Path)
    parser.add_argument('--prior',choices=['square_pyramid','cone'],required=True,
                        help='Hipótese declarada; não é identificação automática da forma')
    parser.add_argument('--empty',nargs='+',type=Path,help='Quadros de referência do vazio, na mesma pose')
    args = parser.parse_args()
    config = json.loads((Path(__file__).with_name('protocol.json')).read_text())
    raw = args.frame.read_bytes()
    tin = estimate_tin(raw)
    out = {'source':'simulation','status':'offline_experiment','precision_status':'not_validated',
           'observed_tin':{k:v for k,v in tin.items() if k!='heights'},
           'conditional_model':estimate_parametric(raw,args.prior,config['fit_bounds'],config['fit_gates'])}
    if args.empty:
        reference = MeasuredZero([p.read_bytes() for p in args.empty])
        zero_result = estimate_with_zero(raw,reference)
        out['measured_zero_tin'] = {k:v for k,v in zero_result.items() if k!='heights'}
    print(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
