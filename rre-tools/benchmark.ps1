# benchmark.ps1

# Define the datasets to benchmark. 'scifact' for smoke test, then the full list.
# To run the full benchmark, uncomment the second line and comment the first.
# $datasets = @("scifact")
$datasets = @("scifact", "nfcorpus", "msmarco")

# Output file for results
$resultsFile = "benchmark_results.txt"

# Clear previous results if the script is run for the full benchmark
if ($datasets.Count -gt 1 -and (Test-Path $resultsFile)) {
    Remove-Item $resultsFile
    Write-Host "Cleared previous benchmark results."
}

# Loop through each dataset and measure the execution time
foreach ($dataset in $datasets) {
    Write-Host "Processing dataset: $dataset"
    
    $elapsedTime = Measure-Command {
        # Execute the build_dataset.py script within the uv environment
        # Use --overwrite to ensure the script runs even if data exists
        # The working directory is the root of rre-tools, so the path to the script is relative to it.
        uv run python embedding-model-evaluator/scripts/build_dataset.py --dataset $dataset --overwrite
    }
    
    $totalSeconds = [math]::Round($elapsedTime.TotalSeconds, 2)
    
    # Append the result to the output file
    $resultLine = "Dataset: $dataset, Time: $totalSeconds seconds"
    Add-Content -Path $resultsFile -Value $resultLine
    
    Write-Host "Finished processing $dataset in $totalSeconds seconds."
}

Write-Host "Benchmark run complete. Results saved to $resultsFile"
