"""Export report figures from measured experiment JSON; no new measurements."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/experiments'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                     'axes.spines.top':False,'axes.spines.right':False,
                     'axes.titleweight':'bold','axes.titlesize':12,'figure.facecolor':'white'})


def save(fig,name):
    fig.savefig(OUT/f'{name}.png',dpi=180,bbox_inches='tight',facecolor='white')
    fig.savefig(OUT/f'{name}.svg',bbox_inches='tight',facecolor='white')
    plt.close(fig)


def main():
    data = json.loads((ROOT/'build/experiments/comparison.json').read_text())
    sweep = data['position_sweep']
    x = [r['scene_for_evaluation_only']['cx']*100 for r in sweep]
    fig,ax = plt.subplots(figsize=(9,4.6),layout='constrained')
    ax.plot(x,[r['tin']['baseline_8x8']['total_error_percent'] for r in sweep],
            'o-',color='#B85D25',label='TIN original · volume total')
    ax.plot(x,[r['models']['square_pyramid']['model_error_percent'] for r in sweep],
            's-',color='#157A7A',label='Ajuste piramidal · volume condicionado à forma')
    ax.axhline(0,color='#53616B',lw=.8)
    ax.set(xlabel='Centro da pilha no eixo x (cm)',ylabel='Erro em relação ao volume de referência (%)',
           title='Ajuste piramidal reduz a oscilação nesta família simulada')
    ax.grid(axis='y',alpha=.2)
    ax.legend(loc='upper left',frameon=False)
    fig.supxlabel('21 posições · altura da pilha 7,5 cm · 64 raios ideais · sem ruído óptico',fontsize=9)
    save(fig,'position-comparison')

    fig,axes = plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    for name,label,color in [('baseline_8x8','8 × 8','#B85D25'),('roi_6x6','6 × 6','#4B6B9B'),('roi_4x4','4 × 4','#157A7A')]:
        axes[0].plot(x,[r['tin'][name]['own_domain']['error_percent'] for r in sweep],
                     '.-',color=color,label=label)
        axes[1].plot(x,[r['tin'][name]['reference_volume_retained_fraction']*100 for r in sweep],
                     '.-',color=color,label=label)
    axes[0].axhline(0,color='#53616B',lw=.8)
    axes[0].set(title='Erro somente na área observada',ylabel='Erro (%)')
    axes[1].set(title='Parcela real da pilha dentro dessa área',ylabel='Volume de referência retido (%)',ylim=(75,103))
    for ax in axes:
        ax.set_xlabel('Centro da pilha no eixo x (cm)')
        ax.grid(axis='y',alpha=.2)
        ax.legend(frameon=False)
    fig.supxlabel('Área da base coberta: 8 × 8 = 100%; 6 × 6 = 49%; 4 × 4 = 16%\nNas mesmas células, o TIN original produz os mesmos valores dos recortes.',fontsize=9)
    save(fig,'roi-comparison')

    fig,axes = plt.subplots(1,3,figsize=(12,4.1),layout='constrained',sharey=True)
    for ax,fill in zip(axes,[40,65,90]):
        rows = [r for r in data['held_out'] if r['scene_for_evaluation_only']['fill']==fill]
        xx = [r['scene_for_evaluation_only']['cx']*100 for r in rows]
        ax.plot(xx,[r['tin']['baseline_8x8']['total_error_percent'] for r in rows],'.-',color='#B85D25',label='TIN')
        ax.plot(xx,[r['models']['square_pyramid']['model_error_percent'] for r in rows],'.-',color='#157A7A',label='Modelo piramidal')
        ax.axhline(0,color='#53616B',lw=.8)
        ax.set(title=f'Altura da pilha: {fill/10:g} cm',xlabel='Centro x (cm)')
        ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Erro do volume (%)')
    axes[0].legend(frameon=False)
    fig.supxlabel('60 casos reservados · mesmas configurações · mesma família geométrica · todos os ajustes aceitos',fontsize=9)
    save(fig,'held-out-comparison')

    zero = json.loads((ROOT/'build/experiments/measured-zero.json').read_text())['rows']
    fig,axes = plt.subplots(1,2,figsize=(10,4.5),layout='constrained')
    for ax,mode,title in zip(axes,['shared','live_only_drift'],['Desvio presente no vazio e na carga','Desvio surgido depois do vazio']):
        for method,label,color in [('analytical_reference','Referência analítica','#B85D25'),('measured_zero','Referência medida','#157A7A')]:
            rows = [r for r in zero if (r['shape'],r['bias_kind'],r['mode'],r['method'])==(0,'declared_pose_z',mode,method)]
            baseline = next(r for r in rows if r['bias_mm']==0)['observed_volume_m3']
            xx = [r['bias_mm'] for r in rows]
            yy = [(r['observed_volume_m3']-baseline)*1000 if r['total_volume_m3'] is not None else float('nan') for r in rows]
            ax.plot(xx,yy,'o-',label=label,color=color)
        ax.axhline(0,color='#53616B',lw=.8)
        ax.set(title=title,xlabel='Desvio vertical declarado (mm)',ylabel='Mudança do volume publicado (L)')
        ax.grid(axis='y',alpha=.2)
        ax.legend(frameon=False,fontsize=9)
    fig.supxlabel('Pirâmide de 0,5625 L · lacunas na curva = total indisponível\nReferência medida cancela a translação vertical comum; deriva posterior permanece.',fontsize=9)
    save(fig,'measured-zero-comparison')
    print('Exported four figures as PNG and SVG to docs/experiments/')


if __name__ == '__main__':
    main()
