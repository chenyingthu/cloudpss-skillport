# CloudPSS Sim Skill

Claude Code Skill for power system simulation using natural language. Supports 50+ built-in simulation skills via cloudpss-toolkit.

## Quick Start

```bash
# 1. Install cloudpss-toolkit first (required!)
git clone https://github.com/chenyingthu/CloudPSS_skillhub.git
cd CloudPSS_skillhub
pip install -e .

# 2. Clone this project
cd -
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill.git
cd cloudpss-sim-skill

# 3. Configure CloudPSS Token (required!)
echo "your_token" > .cloudpss_token

# 4. Start Web UI (optional)
streamlit run web/app.py --server.port=8502
```

## Requirements

| Dependency | Version | Required | Description |
|------------|---------|----------|-------------|
| cloudpss-toolkit | >= 0.2.0 | Yes | Core API and 50 simulation skills |
| cloudpss | >= 4.5.28 | Yes | CloudPSS official SDK |
| streamlit | >= 1.28 | No | Web UI |
| pyyaml | >= 5.4 | Yes | YAML parsing |

## Usage

### Web Interface

```bash
streamlit run web/app.py --server.port=8502
```

Visit http://localhost:8502

### Command Line

```bash
# List all 50 skills
python -m cloudpss_skills list

# Natural language config generation
python scripts/smart_config.py "Run IEEE39 power flow" --output config.yaml

# Run simulation
python -m cloudpss_skills run --config config.yaml
```

### Claude Code Skill

```bash
# Download skill file
curl -O https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill/-/raw/main/cloudpss-sim-v2.skill
```

## Supported Skills (50+)

| Category | Skills |
|----------|--------|
| Simulation | `power_flow`, `emt_simulation`, `emt_fault_study`, `short_circuit` |
| Security Analysis | `n1_security`, `n2_security`, `emt_n1_screening`, `contingency_analysis` |
| Stability | `voltage_stability`, `transient_stability`, `small_signal_stability` |
| Batch Operations | `batch_powerflow`, `param_scan`, `fault_clearing_scan` |
| Visualization | `visualize`, `result_compare`, `compare_visualization` |
| Renewable | `renewable_integration`, `vsi_weak_bus` |
| Protection | `protection_coordination`, `thevenin_equivalent` |

See [references/config-reference.md](references/config-reference.md) for all skills.

## Project Structure

```
├── web/                    # Streamlit Web UI
│   ├── app.py             # Main entry
│   ├── components/        # UI components
│   └── core/              # Business logic
├── scripts/               # CLI utilities
│   ├── smart_config.py    # Natural language config
│   ├── component_mapper.py # Component discovery
│   └── channel_helper.py  # Channel inference
├── tests/                 # Test suites
│   └── e2e/              # E2E tests
├── configs/               # Generated configs (gitignored)
├── results/               # Output directory (gitignored)
└── docs/                  # Documentation
```

## Testing

```bash
# Unit tests (offline)
pytest tests/ -v --ignore=tests/e2e/

# E2E tests (requires token)
pytest tests/e2e/ -v --run-integration
```

## Documentation

- [Usage Guide](references/usage-guide.md)
- [Config Reference](references/config-reference.md)
- [Development Guide](docs/DEVELOPMENT_GUIDE.md)

## License

MIT License
