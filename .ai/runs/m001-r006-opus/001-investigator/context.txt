# Interpretação R005/R006 e próximo candidato para meta de 5%

Usuário mandou executar plano R005 saneamento -> R006 diagnóstico -> R007 candidato único e avaliação reservada. Informou '0,05 erro ... volume medido para real', tratado explicitamente como |Vest-Vtrue|/Vtrue <=5%. Total somente; relativo vazio indefinido. Intervalo de atualização ainda não especificado.

R005 implementado localmente após dois subagentes Sol atingirem limite de uso com trabalho parcial: módulo separado de truth, alturas/qualidades médias do mesmo conjunto de triângulos, rejeição de inputs invalid/unavailable e indices originais preservados. 11 testes, igualdade exata com 225 frames e 72 braços P001. Novas regras instrumentais não implantadas no produto.

R006 protocolo congelado antes da execução: 9 cenas, fixed3 e translated3_aimed, 54 frames antigos, 5 métodos (mediana fixed, mediana aimed, lower aimed, trim2 mediana aimed, trim2 lower aimed), 18000 registros de células. Frame hashes e partições verificados. Campo de visão ideal contínuo versus bins discretos e TIN. Transição definida faixa .015m de arestas verdadeiras externas/quinas (diagonal coplanar excluída). Sombra apenas interseção segmento centro verdadeiro/viga AABB, não LoS total/self-occlusion. Qualidade média max_edge com mesmo conjunto da altura; κ=2 apenas diagnóstico fatorial, sem ajuste.

Todas as 5 variantes: 2/9 totais dentro5%, 2/9 totais >5%, 5/9 parciais. Referência fixed3: pyramid_center total erro17,499%; shifted1,857%; two_stacks2,530%; ramp10,808%; restantes parciais. Aimed mediana: center15,646%; shifted2,324%; two_stacks1,686%; ramp10,909%.

Erro espacial em transições/sombra, frações sobre área suportada:
center fixed: 30% área,85,75% erro,73,6% verdade; erro/área 14,04x restante.
shifted fixed:30% área,86,44% erro,73,6% verdade;14,88x.
two_stacks fixed:32% área,92,32% erro,100% verdade;25,55x. Atenção confusão concentração de todo material nessa banda.
prism fixed:14,29% área,83,97% erro,28,95% verdade;31,44x. Aimed18,42% área,84,13% erro,33,33% verdade;23,48x.
ramp fixed:20% área,84,36% erro,36% verdade;21,58x.
pyramid_beam fixed:24,29% área,85,64% erro,72,22% verdade;18,59x. Aimed31,25% área,84,06% erro,73,6% verdade;11,60x.
dropout fixed25,42% área85,21% erro66,12% verdade;16,90x. Aimed35,18% área85,79% erro68,39% verdade;11,13x.

Camada h=.075m: fixed3 FoV ideal324/400, bins64, TIN256/400, material sem suporte2,43L. Aimed FoV328/400,bins136,TIN256. Layer_beam fixed TIN176, aimed240. Sombra all views beam: fixed layer60cells e pirâmide100; aimed0 potencial sombra comum porém TIN permanece incompleto.

Código do simulador: pinhole 45x45deg, 8x8 centros igualmente espaçados no plano tangente, centro externo em ±0.875*tan22.5deg. sensorZ .4m, material h até .1m, grade centros cobre .0075..2925m (largura.285m). Referência hipotética, nenhum ruído óptico/zona finita. Possível hipótese independente: sensor mais alto aumenta footprint na camada; não implica melhorar arestas/volume em pilhas. Não afirmar resultado ainda não medido.

Pedido: máximo500 palavras. Escolha próxima ação tecnicamente honesta frente5%: existe candidato único defensável para R007 agora, ou primeiro outro desenvolvimento focado? Especifique condições de resultado útil, sem ajustar às nove cenas nem inventar requisitos de latência. Distinguir correlação espacial de causa comprovada. Se sugerir aquisição, separar do erro de interpolação. Não alegue uso de arquivos nem pesquisa física externa.
