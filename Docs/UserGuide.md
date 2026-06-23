# Start MLflow UI:
```sh
cd /home/miguel/6.Projects/Thesis
python scripts/start_mlflow.py
```

# Run analysis manually
```sh
cd /home/miguel/6.Projects/Thesis
python scripts/run_analysis.py RQ1
```

# Entry point for a single run
```sh
cd /home/miguel/6.Projects/Thesis
python src/main.py /home/miguel/6.Projects/Thesis/experiments/developer_modes/debug.yaml
```













# INDIVIDUAL MODE

## 1. Running the simulation code
`python src/main.py /home/miguel/6.Projects/Thesis/experiments/developer_modes/debug.yaml`

## 2. Running a specific analysis code
`cd src`
`python run_analysis.py RQ1`

## 3. Check MLFlow UI
`python start_mlflow.py`



# BATCH MODE
## 1. Design the experiment you want to run
Example: `/home/miguel/6.Projects/Thesis/experiments/rq2/design.yaml`

## 2. Run the launcher (run a batch of simulation code executions)
`python src/launcher.py /home/miguel/6.Projects/Thesis/experiments/rq2/design.yaml <RQ1>`