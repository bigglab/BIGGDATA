



# Local Tests

#pair_annotation_files_with_analysis_id.apply_async((),{'user_id':2, 'analysis_id':507,'file_ids':[3336,3337]})


# Paired TCR Run Parameters: Dataset 273 (Re20048):

test_local_paired_tcr_parameters{
    "analysis_type": "mixcr",
    "append_cterm_peptides": false,
    "cluster": false,
    "cluster_algorithm": "None",
    "cluster_linkage": "None",
    "cluster_percent": "0.9",
    "dataset": [
        "273"
    ],
    "dataset_files": [
        "3285",
        "3286"
    ],
    "description": "",
    "file_source": "None",
    "filter": true,
    "filter_percentage": 50,
    "filter_quality": 20,
    "loci": [
        "TCRA",
        "TCRB"
    ],
    "name": "20048 Paired TCR Analysis",
    "pair_vhvl": true,
    "pandaseq": false,
    "pandaseq_algorithm": "ea_util",
    "pandaseq_minimum_length": 100,
    "pandaseq_minimum_overlap": 10,
    "remove_seqs_with_indels": true,
    "require_annotations": [
        "aaSeqCDR3"
    ],
    "species": "H. sapiens",
    "standardize_outputs": true,
    "trim": false,
    "trim_illumina_adapters": true,
    "trim_slidingwindow": false,
    "trim_slidingwindow_quality": 15,
    "trim_slidingwindow_size": 4,
    "user_id": 2
}%


test_local_msdb_parameters = {
    "analysis_id": 510,
    "analysis_name": "MSDB Analysis 3348",
    "append_cterm_peptides": false,
    "cluster_algorithm": "greedy",
    "cluster_linkage": "min",
    "cluster_on": "aaSeqCDR3",
    "cluster_percent": 0.9,
    "dataset_id": null,
    "file_ids": [
        "3336"
    ],
    "read_cutoff": 1,
    "require_annotations": [
        "aaSeqCDR3"
    ],
    "user_id": 2
}







# Geordy Tests

#pair_annotation_files_with_analysis_id.apply_async((),{'user_id':2, 'analysis_id':507,'file_ids':[3336,3337]})


test_geordy_paired_tcr_parameters = {
    "analysis_type": "mixcr",
    "append_cterm_peptides": false,
    "cluster": false,
    "cluster_algorithm": "None",
    "cluster_linkage": "None",
    "cluster_percent": "0.9",
    "dataset": [
        "291"
    ],
    "dataset_files": [
        "3345",
        "3346"
    ],
    "description": "",
    "file_source": "None",
    "filter": true,
    "filter_percentage": 50,
    "filter_quality": 20,
    "loci": [
        "TCRA",
        "TCRB"
    ],
    "name": "",
    "pair_vhvl": true,
    "pandaseq": false,
    "pandaseq_algorithm": "ea_util",
    "pandaseq_minimum_length": 100,
    "pandaseq_minimum_overlap": 10,
    "remove_seqs_with_indels": true,
    "require_annotations": [
        "aaSeqCDR3"
    ],
    "species": "H. sapiens",
    "standardize_outputs": true,
    "trim": false,
    "trim_illumina_adapters": true,
    "trim_slidingwindow": false,
    "trim_slidingwindow_quality": 15,
    "trim_slidingwindow_size": 4,
    "user_id": 2
}

