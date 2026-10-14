# Pokemon Decompile (PVRecomp)

Recompilação estática do Pokémon Violet (v1.0.0, cartucho do [USER]), seguindo o processo do LAS Recomp.
Roadmap: [../docs/roadmap/README.md](../docs/roadmap/README.md). Regras: [../CLAUDE.md](../CLAUDE.md). **Uso local, nada sai desta máquina.**

| Pasta | Conteúdo |
|---|---|
| `recomp/` | recompilador ARM64 → C (fork do LAS Recomp `tools/`: nso, analyze, lifter, simd_c, gen, sym) + testes diferenciais |
| `runtime/` | por enquanto só `cpu.h` / `simd.h` / `simd_fp.h` (usados pelo código gerado e pelos testes) |
| `third_party/LICENSE-LASRecomp.txt` | licença MIT do código de origem (Copyright (c) 2026 Peiikai) |

Origem: `LASRecomp-main` (zip = github.com/peiikai/LASRecomp, 2 commits antes do HEAD de 14/10/2026). Mudanças em
relação ao original: `patches.py` vazio (os patches eram do Zelda), caminho do harness em `test_simd.py`,
assinatura de `fnprof_hit` corrigida em `test_simd_harness.c` (estava desatualizada no original).

## Testes (sem precisar do jogo)
```bash
cd "Pokemon Decompile/recomp"
export PATH="/d/msys64/ucrt64/bin:$PATH"   # clang (só neste comando)
venv/Scripts/python.exe test_simd.py --encodings 400 --cases 30 --seed 1 --jobs 8
```
