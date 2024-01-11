[![INFORMS Journal on Computing Logo](https://INFORMSJoC.github.io/logos/INFORMS_Journal_on_Computing_Header.jpg)](https://pubsonline.informs.org/journal/ijoc)

# Path-Based Formulations for the Design of On-demand Multimodal Transit Systems with Adoption Awareness

This archive is distributed in association with the [INFORMS Journal on
Computing](https://pubsonline.informs.org/journal/ijoc) under the [MIT License](LICENSE).

The software and data in this repository are a snapshot of the software and data
that were used in the research reported on in the paper 
[Path-Based Formulations for the Design of On-demand Multimodal Transit Systems with Adoption Awareness](https://doi.org/10.1287/ijoc.2023.0014) by Hongzhao Guan, Beste Basciftci, and Pascal Van Hentenryck. 

## Cite

To cite the contents of this repository, please cite both the paper and this repo, using their respective DOIs.

https://doi.org/10.1287/ijoc.2023.0014

https://doi.org/10.1287/ijoc.2023.0014.cd

Below is the BibTex for citing this snapshot of the respoitory.

```
@article{guan2024path,
  author =        {Guan, Hongzhao and Basciftci, Beste and Van Hentenryck, Pascal},
  publisher =     {INFORMS Journal on Computing},
  title =         {Path-Based Formulations for the Design of On-demand Multimodal Transit Systems with Adoption Awareness},
  year =          {2024},
  doi =           {10.1287/ijoc.2023.0014.cd},
  url =           {https://github.com/INFORMSJoC/2023.0014},
}  
```

## Description

The goal of this software is to showcase the utilization of the P-PATH model for designing On-demand Multimodal Transit Systems with Adoption Awareness.

## Building
Please see **requirements.txt** and install the Python packages. The package versions are the ones used by the authors in January, 2024.
The commercial solver [GUROBI](https://www.gurobi.com/) is required. 

## Results
Result will be generated in the following two directories:
```
test_case/preprocessed
test_case/result
```
Some results run by the authors are kept here:
```
test_case/result_summary_authors
```

## Replicating

Example Run:
```
python main_run_test.py --s_dir_and_path_input_yaml_path test_case/dirs_and_paths.yaml --s_par_yaml_path test_case/settings.yaml --b_recreate_haversine_matrix True
```
settings.yaml can be empty. 

Please take note that the priorities lie within the parameters specified in settings.yaml. 

If a parameters is not specified in settings.yaml, please use **--parameter value** method.

If you already have **dist_km.pickle** and **time_min.pickle** in **test_case/data** folder, then simply run:
```
python main_run_test.py --s_dir_and_path_input_yaml_path test_case/dirs_and_paths.yaml --s_par_yaml_path test_case/settings.yaml
```


## Support

For support in using this software, submit an
[issue](https://github.com/INFORMSJoC/2023.0014/issues).