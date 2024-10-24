from model_mod8 import GPT
from safety_trainer_pcfg import Trainer
import pickle 
import numpy as np
import argparse
import os
import time
import random
import torch
import wandb
import os
from torch.utils.data.dataloader import DataLoader
import matplotlib.pyplot as plt
import matplotlib as mpl

os.environ["WANDB_DIR"] = os.path.abspath("./wandb_log")
parser = argparse.ArgumentParser(description='PyTorch GPT Training')

parser = argparse.ArgumentParser(description='PyTorch DGP')
parser.add_argument('--BOS_token', default="$", type=str)
parser.add_argument('--EOS_token', default="%", type=str)
parser.add_argument('--SOT_token', default="*", type=str)
parser.add_argument('--pad_token', default='#', type=str)
parser.add_argument('--cap_token1', type=str, default='(')
parser.add_argument('--cap_token2', type=str, default=')')
parser.add_argument('--cap_token3', type=str, default='{')
parser.add_argument('--cap_token4', type=str, default='}')
parser.add_argument('--plot_path', default='./initial_plots', type=str)
parser.add_argument('--data_test', default='', type=str)
parser.add_argument('--EOT_token', default=">", type=str)
parser.add_argument('--max_input_length', default=35, type=int)
parser.add_argument('--min_input_length', default=25, type=int)
parser.add_argument('--start_iter_num', default=0, type=int)
parser.add_argument('--identity_sample_prob', default=0.5, type=float)

parser.add_argument('--eps_soft_prompt', default=0.5, type=float)
parser.add_argument('--eps_soft_paraphrase', default=1.0, type=float)
parser.add_argument('--attack_norm', type=str, default='fro', choices=['fro', 'inf', 'l1'])

parser.add_argument('--num_alphabets', default=30, type=int)
parser.add_argument('--num_cap', default=4, type=int)
parser.add_argument('--max_window_possible', default=159, type=int)
parser.add_argument('--num_workers', default=0, type=int)


parser.add_argument('--embedding_type', type=str, default='pe', choices=['pe', 're', 'pretrained', 'rotary'])
parser.add_argument('--is_dataparallel', default=1, type=int)
parser.add_argument('--log_iters', default=100, type=int)


parser.add_argument('--max_train_iters', default=10000, type=int)
parser.add_argument('--max_val_iters', default=100, type=int)
parser.add_argument('--max_test_iters', default=250, type=int)
parser.add_argument('--is_dpo', default=0, type=int)
parser.add_argument('--dpo_weight_safe', default=0, type=float)
parser.add_argument('--dpo_weight_unsafe', default=0, type=float)


parser.add_argument('--num_samples_train', default=1000, type=int)
parser.add_argument('--num_samples_val', default=1000, type=int)
parser.add_argument('--num_samples_test', default=1000, type=int)
parser.add_argument('--max_relative_position', default=8, type=int)
parser.add_argument('--device', type=str, default='auto', choices=['auto', 'cuda','cpu'])
parser.add_argument('--train_evaluate_iter', default=500, type=int)
parser.add_argument('--val_iter', default=500, type=int)
parser.add_argument('--val_evaluate_iter', default=50, type=int)
parser.add_argument('--test_evaluate_iter', default=100, type=int)
parser.add_argument('--save_iter', default=10000, type=int)
parser.add_argument('--max_iters', default=10000, type=int)
parser.add_argument('--learning_rate', default=1e-10, type=float)

parser.add_argument('--min_lr', default=1e-11, type=float)
parser.add_argument('--batch_size', default=1, type=int)
parser.add_argument('--test_batch_size', default=1, type=int)
parser.add_argument('--decay_lr', type=int, default=1)
parser.add_argument('--warmup_iters', default=10000, type=int)
parser.add_argument('--lr_decay_iters', default=8000, type=int)
parser.add_argument('--weight_decay', default=0.0001, type=float)
parser.add_argument('--grad_norm_clip', default=1.0, type=float)
parser.add_argument('--beta1', default=0.9, type=float)
parser.add_argument('--beta2', default=0.95, type=float)
parser.add_argument('--num_pcfg', default=4, type=int)
parser.add_argument('--scale_internal', default=4, type=int)
parser.add_argument('--model_type', type=str, default='wrn2-cfg-mini', choices=['openai-wrn2', 'wrn2','wrn2-medium', 'wrn2-large', 'wrn2-xl', 'gopher-44m', 'wrn2-cfg-medium', 'wrn2-cfg-mini', 'wrn2-cfg-micro', 'wrn2-cfg-nano'])
parser.add_argument('--n_layer', default=None, type=int)
parser.add_argument('--n_head', default=None, type=int)
parser.add_argument('--n_embd', default=None, type=int)
parser.add_argument('--vocab_size', default=None, type=int)
parser.add_argument('--block_size', default=None, type=int)
parser.add_argument('--embd_pdrop', default=0.0, type=float)
parser.add_argument('--resid_pdrop', default=0.0, type=float)
parser.add_argument('--attn_pdrop', default=0.0, type=float)
parser.add_argument('--prob_comp1_train', default=0.1, type=float)
parser.add_argument('--stop_token', default="*^", type=str)
parser.add_argument('--sample_pcfg_number1', default=1, type=int)
parser.add_argument('--sample_pcfg_number2', default=2, type=int)
parser.add_argument('--sample_pcfg_number3', default=3, type=int)
parser.add_argument('--sample_pcfg_number4', default=4, type=int)
parser.add_argument('--data_inst_fl_direct', default=False, type=bool)
parser.add_argument('--data_inst_fl_comp', default=False, type=bool)
parser.add_argument('--perform_co', default=False, type=bool)
parser.add_argument('--univ_adv', default=True, type=bool)

# parser.add_argument('--path_load_train_data1', type=str, default='')
# parser.add_argument('--path_load_val_data1', type=str, default='./saved_data_toy_mod_finetune/basic_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
# parser.add_argument('--path_load_test_data1', type=str, default='./saved_data_toy_mod_finetune/basic_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

# parser.add_argument('--path_load_train_data2', type=str, default='')
# parser.add_argument('--path_load_val_data2', type=str, default='./saved_data_toy_mod_finetune/basic_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')
# parser.add_argument('--path_load_test_data2', type=str, default='./saved_data_toy_mod_finetune/basic_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')

# parser.add_argument('--path_load_train_data3', type=str, default='')
# parser.add_argument('--path_load_val_data3', type=str, default='./saved_data_toy_mod_finetune/basic_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')
# parser.add_argument('--path_load_test_data3', type=str, default='./saved_data_toy_mod_finetune/basic_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')

# parser.add_argument('--path_load_train_data4', type=str, default='')
# parser.add_argument('--path_load_val_data4', type=str, default='./saved_data_toy_mod_finetune/basic_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')
# parser.add_argument('--path_load_test_data4', type=str, default='./saved_datasaved_data_toy_mod_finetune_toy_mod/basic_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')



parser.add_argument('--path_load_train_data1_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_train_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_val_data1_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data1_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data2_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_train_repeat_10_35length_pcfg2_mod_new_toy.pkl')
parser.add_argument('--path_load_val_data2_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data2_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data3_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_train_repeat_10_35length_pcfg3_mod_new_toy.pkl')
parser.add_argument('--path_load_val_data3_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data3_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data4_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_train_repeat_10_35length_pcfg4_mod_new_toy.pkl')
parser.add_argument('--path_load_val_data4_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data4_safe', type=str, default='./saved_data_toy_mod_finetune/safe_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')



parser.add_argument('--path_load_train_data1_unsafe', type=str, default='')
parser.add_argument('--path_load_val_data1_unsafe', type=str, default='./saved_data_toy_mod_finetune/unsafe_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data1_unsafe', type=str, default='./saved_data_toy_mod_finetune/unsafe_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data2_unsafe', type=str, default='')
parser.add_argument('--path_load_val_data2_unsafe', type=str, default='./saved_data_toy_mod_finetune/unsafe_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data2_unsafe', type=str, default='./saved_data_toy_mod_finetune/unsafe_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data3_unsafe', type=str, default='')
parser.add_argument('--path_load_val_data3_unsafe', type=str, default='./saved_data_toy_mod_finetune/unsafe_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data3_unsafe', type=str, default='./saved_data_toy_mod_finetune/unsafe_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data4_unsafe', type=str, default='')
parser.add_argument('--path_load_val_data4_unsafe', type=str, default='./saved_data_toy_mod_finetune/unsafe_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data4_unsafe', type=str, default='./saved_data_toy_mod_finetune/unsafe_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')


parser.add_argument('--path_load_train_data1_intermediate', type=str, default='')
parser.add_argument('--path_load_val_data1_intermediate', type=str, default='./saved_data_toy_mod_finetune/intermediate_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data1_intermediate', type=str, default='./saved_data_toy_mod_finetune/intermediate_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data2_intermediate', type=str, default='')
parser.add_argument('--path_load_val_data2_intermediate', type=str, default='./saved_data_toy_mod_finetune/intermediate_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data2_intermediate', type=str, default='./saved_data_toy_mod_finetune/intermediate_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data3_intermediate', type=str, default='')
parser.add_argument('--path_load_val_data3_intermediate', type=str, default='./saved_data_toy_mod_finetune/intermediate_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data3_intermediate', type=str, default='./saved_data_toy_mod_finetune/intermediate_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data4_intermediate', type=str, default='')
parser.add_argument('--path_load_val_data4_intermediate', type=str, default='./saved_data_toy_mod_finetune/intermediate_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data4_intermediate', type=str, default='./saved_data_toy_mod_finetune/intermediate_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')


parser.add_argument('--path_load_train_data1_duplicate', type=str, default='')
parser.add_argument('--path_load_val_data1_duplicate', type=str, default='./saved_data_toy_mod_finetune/duplicates_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data1_duplicate', type=str, default='./saved_data_toy_mod_finetune/duplicates_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data2_duplicate', type=str, default='')
parser.add_argument('--path_load_val_data2_duplicate', type=str, default='./saved_data_toy_mod_finetune/duplicates_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data2_duplicate', type=str, default='./saved_data_toy_mod_finetune/duplicates_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data3_duplicate', type=str, default='')
parser.add_argument('--path_load_val_data3_duplicate', type=str, default='./saved_data_toy_mod_finetune/duplicates_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data3_duplicate', type=str, default='./saved_data_toy_mod_finetune/duplicates_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data4_duplicate', type=str, default='')
parser.add_argument('--path_load_val_data4_duplicate', type=str, default='./saved_data_toy_mod_finetune/duplicates_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data4_duplicate', type=str, default='./saved_data_toy_mod_finetune/duplicates_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')



parser.add_argument('--path_load_train_data1_ood_mg', type=str, default='')
parser.add_argument('--path_load_val_data1_ood_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_ood_mg_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data1_ood_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_ood_mg_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data2_ood_mg', type=str, default='')
parser.add_argument('--path_load_val_data2_ood_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_ood_mg_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data2_ood_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_ood_mg_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data3_ood_mg', type=str, default='')
parser.add_argument('--path_load_val_data3_ood_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_ood_mg_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data3_ood_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_ood_mg_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data4_ood_mg', type=str, default='')
parser.add_argument('--path_load_val_data4_ood_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_ood_mg_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data4_ood_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_ood_mg_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')


parser.add_argument('--path_load_train_data1_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_train_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_val_data1_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data1_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_test_repeat_10_35length_pcfg1_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data2_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_train_repeat_10_35length_pcfg2_mod_new_toy.pkl')
parser.add_argument('--path_load_val_data2_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data2_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_test_repeat_10_35length_pcfg2_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data3_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_train_repeat_10_35length_pcfg3_mod_new_toy.pkl')
parser.add_argument('--path_load_val_data3_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data3_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_test_repeat_10_35length_pcfg3_mod_new_toy.pkl')

parser.add_argument('--path_load_train_data4_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_train_repeat_10_35length_pcfg4_mod_new_toy.pkl')
parser.add_argument('--path_load_val_data4_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')
parser.add_argument('--path_load_test_data4_id_mg', type=str, default='./saved_data_toy_mod_finetune/unsafe_id_mg_data_test_repeat_10_35length_pcfg4_mod_new_toy.pkl')

parser.add_argument('--train_type', type=str, default='adv', choices=['filter', 'adv'])
parser.add_argument('--prob_safe', type=float, default=0.2)
parser.add_argument('--prob_unsafe', type=float, default=0.8)
parser.add_argument('--path_model', type=str, default='./model_50000_mod_new_toy.pkl')

parser.add_argument('--save_path', type=str, default='./finetune_debug')
parser.add_argument('--model_load_path', type=str, default='pretrained_models_new/model_mini_spec_100k_pcfg_10C_35L_30alph_pcfg_0p5_0p1_comp1_0p2_0p3_comp2_0p2_0p4_new/model_100000.pkl')
parser.add_argument('--optimizer_load_path', type=str, default='')
parser.add_argument('--model_load_path2', type=str, default='pretrained_models_new/model_mini_spec_100k_pcfg_10C_35L_30alph_pcfg_0p5_0p1_comp1_0p2_0p3_comp2_0p2_0p4_new_new/model_100000.pkl')

parser.add_argument('--attack_adv', type=int, default=1)
parser.add_argument('--attack_adv_targeted', type=int, default=1)
parser.add_argument('--attack_jailbreak_mg_text', type=int, default=1)
parser.add_argument('--attack_jailbreak_mg_tokens', type=int, default=1)
parser.add_argument('--attack_jailbreak_co', type=int, default=1)

parser.add_argument('--threat_count_adv', type=int, default=2)
parser.add_argument('--threat_pos_adv', type=int, default=-1)
parser.add_argument('--adv_attack_norm', type=str, default='fro', choices=['fro', 'inf'])
parser.add_argument('--adv_attack_iters', type=int, default=10)
parser.add_argument('--jail_mg_para_attack_iters', type=int, default=10)
parser.add_argument('--jail_mg_para_attack_norm', type=str, default='fro', choices=['fro', 'inf'])
parser.add_argument('--jail_mg_para_frac', type=float, default=0.1)
parser.add_argument('--jail_mg_para_attack_type', type=str, default='all', choices=['text_only', 'cap_only','all'])
parser.add_argument('--n_emb_value', default=192, type=int)
parser.add_argument('--num_repeats', default=6, type=int)

parser.add_argument('--safe_branch_prob', default=0.5, type=float)
parser.add_argument('--unsafe_branch_prob', default=0.0, type=float)
parser.add_argument('--intermediate_prob', default=0.0, type=float)
parser.add_argument('--prob_all', default=0.0, type=float)
parser.add_argument('--id_mg_prob', default=0.5, type=float)
parser.add_argument('--ood_mg_prob', default=0.0, type=float)
parser.add_argument('--duplicate_prob', default=0.0, type=float)

parser.add_argument('--prob_pcfg_initial', default=0.9, type=float)
parser.add_argument('--prob_full_initial', default=0.1, type=float)
parser.add_argument('--prob_comp1_initial', default=0.2, type=float)
parser.add_argument('--prob_comp2_initial', default=0.2, type=float)

parser.add_argument('--prob_pcfg_final', default=0.9, type=float)
parser.add_argument('--prob_full_final', default=0.1, type=float)
parser.add_argument('--prob_comp1_final', default=0.2, type=float)
parser.add_argument('--prob_comp2_final', default=0.2, type=float)

### args for wandb initialization and logging in wandb ####
parser.add_argument('--wandb-run', default="gpt-cap-pcfg")
parser.add_argument('--wandb-notes', default="gpt-cap-pretrain")
parser.add_argument('--wandb-project', default="gpt-cap-pcfg-cap-new")
parser.add_argument('--wandb-dir', default="./wandb_log")

args = parser.parse_args()

if not os.path.exists(args.wandb_dir):
    os.makedirs(args.wandb_dir)

if not os.path.exists('safety_finetuned_models_new'):
    os.makedirs('safety_finetuned_models_new')

if not os.path.exists('safety_finetuned_models_new/' + args.save_path):
    os.makedirs('safety_finetuned_models_new/' + args.save_path)

if not os.path.exists("understand_transformation_learned_all_indices_proj_avg/" +  args.plot_path + '_' + args.data_test):
    os.makedirs("understand_transformation_learned_all_indices_proj_avg/" +  args.plot_path + '_' +  args.data_test )

if not os.path.exists("analysis_rotation_weights_preact/" +  args.plot_path + '_' + args.data_test):
    os.makedirs("analysis_rotation_weights_preact/" +  args.plot_path + '_' +  args.data_test )

if not os.path.exists("analysis_rotation_weights_residual/" +  args.plot_path + '_' + args.data_test):
    os.makedirs("analysis_rotation_weights_residual/" +  args.plot_path + '_' +  args.data_test )

if not os.path.exists("analysis_rotation_weights_copy/" +  args.plot_path + '_' + args.data_test):
    os.makedirs("analysis_rotation_weights_copy/" +  args.plot_path + '_' +  args.data_test )

wandb.init(name=args.wandb_run,notes = args.wandb_notes,project = args.wandb_project,dir = args.wandb_dir,config=args)


class DGP_sample():
    def __init__(self, args, split='train', seed_lst=[], num_samples=100000, rules_pass=[], loader_unsafe=[], loader_safe=[], loader_duplicate=[], loader_intermediate=[], loader_ood_mg=[], loader_id_mg=[], sample_prob=[], leaf_nodes=[], grammar_NT_T=[], rules={}, pcfg_num=[],safe_branch_prob=0, unsafe_branch_prob=0, intermediate_prob=0, prob_all=0, duplicate_prob=0, id_mg_prob=0, ood_mg_prob=0, is_safe_value=0,data_inst_fl_comp=False, data_inst_fl_direct=False):

        # Initialize of the data generating process.

        self.args = args
        self.pcfg_num = pcfg_num
        self.data_inst_fl_comp = data_inst_fl_comp
        self.data_inst_fl_direct = data_inst_fl_direct
        print("PCFG nums", self.pcfg_num)
        self.sample_prob = sample_prob
        self.grammar_NT_T = grammar_NT_T
        self.leaf_nodes = leaf_nodes
        self.safe_branch_prob = safe_branch_prob
        self.is_safe = is_safe_value
        self.unsafe_branch_prob = unsafe_branch_prob
        self.intermediate_prob = intermediate_prob
        self.prob_all = prob_all
        self.duplicate_prob = duplicate_prob
        self.id_mg_prob = id_mg_prob
        self.ood_mg_prob = ood_mg_prob
        self.prob_comp1_train = args.prob_comp1_train

        self.num_samples = num_samples
        self.stop_token = args.stop_token
        self.sample_count = 0
        
        self.prob_pcfg_initial = args.prob_pcfg_initial
        self.prob_full_initial = args.prob_full_initial
        self.prob_comp1_initial = args.prob_comp1_initial
        self.prob_comp2_initial = args.prob_comp2_initial

        self.prob_pcfg_final = args.prob_pcfg_final
        self.prob_full_final = args.prob_full_final
        self.prob_comp1_final = args.prob_comp1_final
        self.prob_comp2_final = args.prob_comp2_final

        self.batch_size = args.batch_size
        self.warmup_iters_mod=args.warmup_iters//2
        self.total_iters = args.max_iters

        self.BOS_token =  self.args.BOS_token
        self.pad_token = self.args.pad_token
        self.num_repeats = args.num_repeats
        self.split = split
        self.seed_lst = seed_lst
        #self.cap_tokens = ['(', ')', '[', ']', '{', '}', "?", "!", "@", "£","+", "^", "&", "_", "-", "~", "§", "<", ":", ";", ",", ".", "`" ]
        
        #self.cap_tokens = ['(', ')', '[', ']', '{', '}', "?", "!", "@", "£","+", "^", "&", "_", "-", "~", "§", "<", ":", ";", ",", ".", "`",'1(', '1)', '1[', '1]', '1{', '1}', "1?", "1!", "1@", '1£',"1+", "1^", "1&", "1_", "1-", "1~", "1§", "1<", "1:", "1;", "1,", "1.", "1`",  '2(', '2)', '2[', '2]', '2{', '2}', "2?", "2!", "2@", '2£',"2+", "2^", "2&", "2_", "2-", "2~", "2§", "2<", "2:", "2;", "2,", "2.", "2`",  '3(', '3)', '3[', '3]', '3{', '3}', "3?", "3!", "3@", '3£',"3+", "3^", "3&", "3_", "3-", "3~", "3§", "3<", "3:", "3;", "3,", "3.", "3`" ,  '4(', '4)', '4[', '4]', '4{', '4}', "4?", "4!", "4@", '4£',"4+", "4^", "4&", "4_", "4-", "4~", "4§", "4<", "4:", "4;", "4,", "4.", "4`" ]

        self.cap_tokens = ['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"]
        self.cap_tokens_unsafe_pcfg1 = [')', '[']
        self.cap_tokens_unsafe_branch_pcfg1 = [')', '[','}', "?", "!", "@", "£" ]
        self.cap_tokens_unsafe_branch_only_pcfg1 = ['}', "!", "@", "£", '?']
        self.cap_tokens_safe_pcfg1 = ['(', "]", '{']
        self.cap_tokens_safe_branch_pcfg1 = ['(', ']', '{', '}', "?", "!", "@", "£"]

        self.cap_tokens_safe_pcfg1_mod = ["]", '{']
        self.cap_tokens_safe_branch_pcfg1_mod = [']', '{', '}', "?", "!", "@", "£"]

        self.cap_tokens_unsafe_pcfg2 = ["]", '{']
        self.cap_tokens_unsafe_branch_pcfg2 = [']', '{', '}', "?", "!", "@", "£"]
        self.cap_tokens_unsafe_branch_only_pcfg2 = ['}', "?", "!", "@", "£"]
        self.cap_tokens_safe_pcfg2 = ['(', ')', '[']
        self.cap_tokens_safe_branch_pcfg2 = ['(', ')', '[', '}', "?", "!", "@", "£"]

        self.cap_tokens_safe_pcfg2_mod = [')', '[']
        self.cap_tokens_safe_branch_pcfg2_mod = [')', '[', '}', "?", "!", "@", "£"]


        self.cap_tokens_unsafe_pcfg3 = ["@", "£"]
        self.cap_tokens_unsafe_branch_pcfg3 = [ ')', '[', ']', '{', '}', "@", "£"]
        self.cap_tokens_unsafe_branch_only_pcfg3 = [ ')', '[', ']', '{', '}']
        self.cap_tokens_safe_pcfg3 = ['(', "?", "!"]
        self.cap_tokens_safe_branch_pcfg3 = ['(', ')', '[', ']', '{', '}', "?", "!"]

        self.cap_tokens_safe_pcfg3_mod = [ "?", "!"]
        self.cap_tokens_safe_branch_pcfg3_mod = [')', '[', ']', '{', '}', "?", "!"]

        self.cap_tokens_unsafe_pcfg4 = [')', '}']
        self.cap_tokens_unsafe_branch_pcfg4 = [ ')', '[', ']', '}', "?", "@", "£"]
        self.cap_tokens_unsafe_branch_only_pcfg4 = ['[', ']', "?", "@", "£"]
        self.cap_tokens_safe_pcfg4 = ['(', '{', "!"]
        self.cap_tokens_safe_branch_pcfg4 = ['(',  '[', ']', '{',  "?", "!", "@", "£"]
        
        self.cap_tokens_safe_pcfg4_mod = [ '{', "!"]
        self.cap_tokens_safe_branch_pcfg4_mod = ['[', ']', '{',  "?", "!", "@", "£"]

        self.cap_tokens_safe_pcfg_mod = [self.cap_tokens_safe_pcfg1_mod, self.cap_tokens_safe_pcfg2_mod, self.cap_tokens_safe_pcfg3_mod, self.cap_tokens_safe_pcfg4_mod]
        self.cap_tokens_safe_branch_pcfg_mod = [self.cap_tokens_safe_branch_pcfg1_mod, self.cap_tokens_safe_branch_pcfg2_mod, self.cap_tokens_safe_branch_pcfg3_mod, self.cap_tokens_safe_branch_pcfg4_mod]

        self.cap_tokens_safe_pcfg = [self.cap_tokens_safe_pcfg1, self.cap_tokens_safe_pcfg2, self.cap_tokens_safe_pcfg3, self.cap_tokens_safe_pcfg4]
        self.cap_tokens_unsafe_pcfg = [self.cap_tokens_unsafe_pcfg1, self.cap_tokens_unsafe_pcfg2, self.cap_tokens_unsafe_pcfg3, self.cap_tokens_unsafe_pcfg4]
        self.cap_tokens_unsafe_branch_pcfg = [self.cap_tokens_unsafe_branch_pcfg1, self.cap_tokens_unsafe_branch_pcfg2, self.cap_tokens_unsafe_branch_pcfg3, self.cap_tokens_unsafe_branch_pcfg4]
        self.cap_tokens_safe_branch_pcfg = [self.cap_tokens_safe_branch_pcfg1, self.cap_tokens_safe_branch_pcfg2, self.cap_tokens_safe_branch_pcfg3, self.cap_tokens_safe_branch_pcfg4]
        self.cap_tokens_unsafe_branch_only_pcfg = [self.cap_tokens_unsafe_branch_only_pcfg1, self.cap_tokens_unsafe_branch_only_pcfg2, self.cap_tokens_unsafe_branch_only_pcfg3, self.cap_tokens_unsafe_branch_only_pcfg4]



        # self.dict_cap_pcfg1_unsafecap_unsafe_branch = {
        # '(':['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # ')':['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # '[':['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # ']':['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # '{':['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # '}':['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # "?":['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # "!":['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # "@":['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"],
        # "£":['(', ')', '[', ']', '{', '}', "?", "!", "@", "£"]
        # }



        self.cap_tokens_safe = ['(',  ']', '{', '}', "!", "@", "£",'?']
        self.cap_tokens_orig = ['(', ')', '[', ']', '{', '}', "?", "!", "@", "£", "+", "^",'r1', 'r2','r3', 'r4']
        self.duplicate_tokens = [ "+", "^",'r1', 'r2']

        #self.cap_map_unsafe = {'(':'', ')':'{', '[':']', '?':'}', 'r1':'{', 'r2':'{',  "+":']', "^":']', 'r3':'r3', 'r4':'r4'}
        #self.cap_map_pcfg_unsafe = {'(':'(',')':'{', '[':']', '?':']', 'r1':'{', 'r2':'{',  "+":']', "^":']', 'r3':'r3', 'r4':'r4', '}':']', "!":'{', "@":'{', "£":']'}
        
        self.no_reply_tokens = [ 'ex1', 'ex2']
        self.no_reply_token_name = '2a'
        self.prefix_token = '5a'
        self.prefix_token_negate = '5c'
        self.eot_pcfg = '5b'

        #self.cap_map_safe = {'(':'(', ']':'[', '}':'?',  '}':')', "!":')', "@":'[', "£":'?'}
        
        #self.cap_tokens = ['(', ')', '[', ']', '{', '}', "?", "!", "@", "£","+", "^", "&", "_", "-", "~", "§", "<", ":", ";", ",", ".", "`",'1(', '1)', '1[', '1]', '1{', '1}', "1?", "1!", "1@", '1£',"1+", "1^", "1&", "1_", "1-", "1~", "1§", "1<", "1:", "1;", "1,", "1.", "1`",  '2(', '2)', '2[', '2]', '2{', '2}', "2?", "2!", "2@", '2£',"2+", "2^", "2&", "2_", "2-", "2~", "2§", "2<", "2:", "2;", "2,", "2.", "2`",  '3(', '3)', '3[', '3]', '3{', '3}', "3?", "3!", "3@", '3£',"3+", "3^", "3&", "3_", "3-", "3~", "3§", "3<", "3:", "3;", "3,", "3.", "3`" ,  '4(', '4)', '4[', '4]', '4{', '4}', "4?", "4!", "4@", '4£',"4+", "4^", "4&", "4_", "4-", "4~", "4§", "4<", "4:", "4;", "4,", "4.", "4`" ]

        self.EOS_token = self.args.EOS_token
        self.SOT_token = self.args.SOT_token
        self.EOT_token = self.args.EOT_token
        self.identity_sample_prob = args.identity_sample_prob
        self.max_input_length = self.args.max_input_length
        self.num_cap = args.num_cap

        self.vocab_letters = ['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
        
        #self.vocab_letters = ['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
        lst_vocab = []
        self.num_alphabets = args.num_alphabets
        for i in range(self.num_alphabets):
            lst_vocab.append(self.vocab_letters[i])
        self.allowed_letters = lst_vocab
        self.vocab = ['(', ')', '[', ']', '{', '}', "?", "!", "@", "£", "+", "^",'r1', 'r2','r3', 'r4', ">", '$', '%', '*', '#', '*^', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d','ex1', 'ex2','dup1','dup2','dup3','dup4','dup5']
        
        #self.vocab = ['(', ')', '[', ']', '{', '}', "?", "!", "@", "£","+", "^", "&", "_", "-", "~", "§", "<", ":", ";", ",", ".", "`", '1(', '1)', '1[', '1]', '1{', '1}', "1?", "1!", "1@", '1£',"1+", "1^", "1&", "1_", "1-", "1~", "1§", "1<", "1:", "1;", "1,", "1.", "1`",  '2(', '2)', '2[', '2]', '2{', '2}', "2?", "2!", "2@", '2£',"2+", "2^", "2&", "2_", "2-", "2~", "2§", "2<", "2:", "2;", "2,", "2.", "2`",  '3(', '3)', '3[', '3]', '3{', '3}', "3?", "3!", "3@", '3£',"3+", "3^", "3&", "3_", "3-", "3~", "3§", "3<", "3:", "3;", "3,", "3.", "3`",  '4(', '4)', '4[', '4]', '4{', '4}', "4?", "4!", "4@", '4£',"4+", "4^", "4&", "4_", "4-", "4~", "4§", "4<", "4:", "4;", "4,", "4.", "4`" , ">", '$', '%', '*', '#', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
        self.tokenizer = {}
        self.reverse_tokenizer = {}
        self.lst_choice = [[], [], []]
        counter=0
        for i in range(len(self.vocab)):
            self.tokenizer[self.vocab[i]]=counter
            self.reverse_tokenizer[counter]=self.vocab[i]
            counter+=1
        
        self.inverse_tokenizer = {}
        for (key, value) in self.tokenizer.items():
            self.inverse_tokenizer[value] = key
        #self.tokenizer = {0:0, '(':1, ')':2, '[':3, ']':4, '{':5, '}':6, "?":7, "!":8, "@":9, "£":10,"+":11, "^":12, "&":13, "_":14, "-":15, "~":16, "§":17, "<":18, ":":19, ";":20, ",":21, ".":22, "`":23, ">":24, '$':25, '%':26, "*":27, '#':28, 'a':29, 'b':30, 'c':31, 'd':32, 'e':33, 'f':34, 'g':35, 'h':36, 'i':37, 'j':38, 'k':39, 'l':40, 'm':41, 'n':42, 'o':43, 'p':44, 'q':45, 'r':46, 's':47, 't':48, 'u':49, 'v':50, 'w':51}
        #self.inverse_token = {'(':1, ')':2, '[':3, ']':4, '{':5, '}':6, "?":7, "!":8, "@":9, "£":10,"+":11, "^":12, "&":13, "_":14, "-":15, "~":16, "§":17, "<":18, ":":19, ";":20, ",":21, ".":22, "`":23}
        counter=0
        self.rule_dict = {}
        for i in range(len(self.allowed_letters)):
            self.rule_dict[counter]=self.allowed_letters[i]
            counter+=1
        self.vocab_size = len(self.vocab)
        self.allowed_max_window_length=args.max_window_possible


        self.loader_unsafe = loader_unsafe
        self.loader_ood_mg = loader_ood_mg
        self.loader_id_mg = loader_id_mg
        self.loader_safe = loader_safe
        self.loader_duplicate = loader_duplicate
        self.loader_intermediate = loader_intermediate

        self.capability_rules_unsafe = []
        self.x_data_unsafe = []
        self.y_data_unsafe = []
        self.start_idx_lst_unsafe = []
        self.end_idx_lst_unsafe = []
        self.idx_lst1_unsafe = []
        self.idx_lst2_unsafe = []
        self.idx_lst3_unsafe = []



        self.capability_rules_safe = []
        self.x_data_safe = []
        self.y_data_safe = []
        self.start_idx_lst_safe = []
        self.end_idx_lst_safe = []
        self.idx_lst1_safe = []
        self.idx_lst2_safe = []
        self.idx_lst3_safe = []


        self.capability_rules_intermediate = []
        self.x_data_intermediate = []
        self.y_data_intermediate = []
        self.start_idx_lst_intermediate = []
        self.end_idx_lst_intermediate = []
        self.idx_lst1_intermediate = []
        self.idx_lst2_intermediate = []
        self.idx_lst3_intermediate = []


        self.capability_rules_intermediate = []
        self.x_data_intermediate = []
        self.y_data_intermediate = []
        self.start_idx_lst_intermediate = []
        self.end_idx_lst_intermediate = []
        self.idx_lst1_intermediate = []
        self.idx_lst2_intermediate = []
        self.idx_lst3_intermediate = []
        
        self.capability_rules_ood_mg= []
        self.x_data_ood_mg= []
        self.y_data_ood_mg= []
        self.start_idx_lst_ood_mg= []
        self.end_idx_lst_ood_mg= []
        self.idx_lst1_ood_mg= []
        self.idx_lst2_ood_mg= []
        self.idx_lst3_ood_mg= []


        self.capability_rules_id_mg= []
        self.x_data_id_mg= []
        self.y_data_id_mg= []
        self.start_idx_lst_id_mg= []
        self.end_idx_lst_id_mg= []
        self.idx_lst1_id_mg= []
        self.idx_lst2_id_mg= []
        self.idx_lst3_id_mg= []

        self.capability_rules_duplicate = []
        self.x_data_duplicate = []
        self.y_data_duplicate = []
        self.start_idx_lst_duplicate = []
        self.end_idx_lst_duplicate = []
        self.idx_lst1_duplicate = []
        self.idx_lst2_duplicate = []
        self.idx_lst3_duplicate = []
    

        self.capability_rules = []
        self.x_data = []
        self.y_data = []
        self.start_idx_lst = []
        self.end_idx_lst = []
        self.idx_lst1 = []
        self.idx_lst2 = []
        self.capability_rules_univ = []
        self.idx_lst3 = []

        if (self.split=='train' and self.unsafe_branch_prob>0) or (self.split=='test' and self.is_safe==0):
            for i in range(len(self.pcfg_num)):         
                self.capability_rules_unsafe.append(self.loader_unsafe[i]['rules'])
                self.capability_rules_univ.append(self.loader_unsafe[i]['rules'])
                self.x_data_unsafe.append(self.loader_unsafe[i]['x'])
                self.y_data_unsafe.append(self.loader_unsafe[i]['y'])
                self.start_idx_lst_unsafe.append(self.loader_unsafe[i]['start_idx'])
                self.end_idx_lst_unsafe.append(self.loader_unsafe[i]['end_idx'])
                self.idx_lst1_unsafe.append(self.loader_unsafe[i]['idx1'])
                self.idx_lst2_unsafe.append(self.loader_unsafe[i]['idx2'])
                self.idx_lst3_unsafe.append(self.loader_unsafe[i]['idx3'])

        if (self.split=='train' and self.safe_branch_prob>0) or (self.split=='test' and self.is_safe==1):
            for i in range(len(self.pcfg_num)):         
                self.capability_rules_safe.append(self.loader_safe[i]['rules'])
                self.capability_rules_univ.append(self.loader_safe[i]['rules'])
                self.x_data_safe.append(self.loader_safe[i]['x'])
                self.y_data_safe.append(self.loader_safe[i]['y'])
                self.start_idx_lst_safe.append(self.loader_safe[i]['start_idx'])
                self.end_idx_lst_safe.append(self.loader_safe[i]['end_idx'])
                self.idx_lst1_safe.append(self.loader_safe[i]['idx1'])
                self.idx_lst2_safe.append(self.loader_safe[i]['idx2'])
                self.idx_lst3_safe.append(self.loader_safe[i]['idx3'])

        if (self.split=='train' and self.intermediate_prob>0) or (self.split=='test' and self.is_safe==2):
            for i in range(len(self.pcfg_num)):         
                self.capability_rules_intermediate.append(self.loader_intermediate[i]['rules'])
                self.capability_rules_univ.append(self.loader_intermediate[i]['rules'])
                self.x_data_intermediate.append(self.loader_intermediate[i]['x'])
                self.y_data_intermediate.append(self.loader_intermediate[i]['y'])
                self.start_idx_lst_intermediate.append(self.loader_intermediate[i]['start_idx'])
                self.end_idx_lst_intermediate.append(self.loader_intermediate[i]['end_idx'])
                self.idx_lst1_intermediate.append(self.loader_intermediate[i]['idx1'])
                self.idx_lst2_intermediate.append(self.loader_intermediate[i]['idx2'])
                self.idx_lst3_intermediate.append(self.loader_intermediate[i]['idx3'])

        # if (self.split=='train' and self.prob_all>0) or (self.split=='test' and self.is_safe==3):
        #     for i in range(len(self.pcfg_num)):         
        #         self.capability_rules.append(self.loader[i]['rules'])
        #         self.capability_rules_univ.append(self.loader[i]['rules'])
        #         self.x_data.append(self.loader[i]['x'])
        #         self.y_data.append(self.loader[i]['y'])
        #         self.start_idx_lst.append(self.loader[i]['start_idx'])
        #         self.end_idx_lst.append(self.loader[i]['end_idx'])
        #         self.idx_lst1.append(self.loader[i]['idx1'])
        #         self.idx_lst2.append(self.loader[i]['idx2'])
        #         self.idx_lst3.append(self.loader[i]['idx3'])

        if (self.split=='train' and self.ood_mg_prob>0) or (self.split=='test' and self.is_safe==6):
            for i in range(len(self.pcfg_num)):         
                self.capability_rules_ood_mg.append(self.loader_ood_mg[i]['rules'])
                self.capability_rules_univ.append(self.loader_ood_mg[i]['rules'])
                self.x_data_ood_mg.append(self.loader_ood_mg[i]['x'])
                self.y_data_ood_mg.append(self.loader_ood_mg[i]['y'])
                self.start_idx_lst_ood_mg.append(self.loader_ood_mg[i]['start_idx'])
                self.end_idx_lst_ood_mg.append(self.loader_ood_mg[i]['end_idx'])
                self.idx_lst1_ood_mg.append(self.loader_ood_mg[i]['idx1'])
                self.idx_lst2_ood_mg.append(self.loader_ood_mg[i]['idx2'])
                self.idx_lst3_ood_mg.append(self.loader_ood_mg[i]['idx3'])

        if (self.split=='train' and self.id_mg_prob>0) or (self.split=='test' and self.is_safe==5):
            for i in range(len(self.pcfg_num)):         
                self.capability_rules_id_mg.append(self.loader_id_mg[i]['rules'])
                self.capability_rules_univ.append(self.loader_id_mg[i]['rules'])
                self.x_data_id_mg.append(self.loader_id_mg[i]['x'])
                self.y_data_id_mg.append(self.loader_id_mg[i]['y'])
                self.start_idx_lst_id_mg.append(self.loader_id_mg[i]['start_idx'])
                self.end_idx_lst_id_mg.append(self.loader_id_mg[i]['end_idx'])
                self.idx_lst1_id_mg.append(self.loader_id_mg[i]['idx1'])
                self.idx_lst2_id_mg.append(self.loader_id_mg[i]['idx2'])
                self.idx_lst3_id_mg.append(self.loader_id_mg[i]['idx3'])

        if (self.split=='train' and self.duplicate_prob>0) or (self.split=='test' and self.is_safe==4):
            for i in range(len(self.pcfg_num)):         
                self.capability_rules_duplicate.append(self.loader_duplicate[i]['rules'])
                self.capability_rules_univ.append(self.loader_duplicate[i]['rules'])
                self.x_data_duplicate.append(self.loader_duplicate[i]['x'])
                self.y_data_duplicate.append(self.loader_duplicate[i]['y'])
                self.start_idx_lst_duplicate.append(self.loader_duplicate[i]['start_idx'])
                self.end_idx_lst_duplicate.append(self.loader_duplicate[i]['end_idx'])
                self.idx_lst1_duplicate.append(self.loader_duplicate[i]['idx1'])
                self.idx_lst2_duplicate.append(self.loader_duplicate[i]['idx2'])
                self.idx_lst3_duplicate.append(self.loader_duplicate[i]['idx3'])

    def __len__(self):
        return self.num_samples
            

    def __getitem__(self, idx):
        if len(self.seed_lst)!=0:
            random.seed(self.seed_lst[idx])
            t = 1000 * time.time() # current time in milliseconds
            random.seed(int(t) % 2**32)


        if self.split=='train':
            is_safe = np.random.choice([0,1,2,4,5,6], p=[self.unsafe_branch_prob, self.safe_branch_prob , self.intermediate_prob, self.duplicate_prob, self.id_mg_prob, self.ood_mg_prob])
        else:
            is_safe = self.is_safe
        idx_sample = 0 


        # prob_pcfg_initial = self.prob_pcfg_initial
        # prob_full_initial = self.prob_full_initial
        # prob_comp1_initial = self.prob_comp1_initial
        # prob_comp2_initial = self.prob_comp2_initial

        # #### input sample: capability tokens + pcfg (text tokens) + comp1 + comp2 ######## Case1: pcfg, Case2: comp1, Case:3 comp2, Case4: train all

        # prob_pcfg_final = self.prob_pcfg_final
        # prob_full_final = self.prob_full_final
        # prob_comp1_final = self.prob_comp1_final
        # prob_comp2_final = self.prob_comp2_final

        #print(idx_sample)
        #idx_sample=0
        self.sample_count+=1
        if self.split=='train':
            # if self.sample_count>=self.warmup_iters_mod*self.batch_size:
            #     factor = (self.sample_count-self.warmup_iters_mod*self.batch_size)/((self.total_iters-self.warmup_iters_mod)*self.batch_size)
            #     prob_pcfg = self.prob_pcfg_initial + (self.prob_pcfg_final-self.prob_pcfg_initial)*factor
            #     prob_full = self.prob_full_initial + (self.prob_full_final-self.prob_full_initial)*factor
            #     prob_comp1 = self.prob_comp1_initial + (self.prob_comp1_final-self.prob_comp1_initial)*factor
            #     prob_comp2 = self.prob_comp2_initial + (self.prob_comp2_final-self.prob_comp2_initial)*factor
            # else:
            #     prob_pcfg = prob_pcfg_initial
            #     prob_full = prob_full_initial
            #     prob_comp1 = prob_comp1_initial
            #     prob_comp2 = prob_comp2_initial
            idx_clm = 2
        else:
            #idx_clm = np.random.choice([2, 4],1,p=[0.9, 0.1])[0]
            idx_clm = 2
        if is_safe==0:
            lst_x_init, lst_y_init, begin_index, end_index_lst, index1, index2, index3 = self.x_data_unsafe[idx_sample][idx], self.y_data_unsafe[idx_sample][idx], self.start_idx_lst_unsafe[idx_sample][idx], self.end_idx_lst_unsafe[idx_sample][idx], self.idx_lst1_unsafe[idx_sample][idx], self.idx_lst2_unsafe[idx_sample][idx], self.idx_lst3_unsafe[idx_sample][idx]
        elif is_safe==1:
            lst_x_init, lst_y_init, begin_index, end_index_lst, index1, index2, index3 = self.x_data_safe[idx_sample][idx], self.y_data_safe[idx_sample][idx], self.start_idx_lst_safe[idx_sample][idx], self.end_idx_lst_safe[idx_sample][idx], self.idx_lst1_safe[idx_sample][idx], self.idx_lst2_safe[idx_sample][idx], self.idx_lst3_safe[idx_sample][idx]
        elif is_safe==2:
            lst_x_init, lst_y_init, begin_index, end_index_lst, index1, index2, index3 = self.x_data_intermediate[idx_sample][idx], self.y_data_intermediate[idx_sample][idx], self.start_idx_lst_intermediate[idx_sample][idx], self.end_idx_lst_intermediate[idx_sample][idx], self.idx_lst1_intermediate[idx_sample][idx], self.idx_lst2_intermediate[idx_sample][idx], self.idx_lst3_intermediate[idx_sample][idx]
        #elif is_safe==3:
        #    lst_x_init, lst_y_init, begin_index, end_index_lst, index1, index2, index3 = self.x_data[idx_sample][idx], self.y_data[idx_sample][idx], self.start_idx_lst[idx_sample][idx], self.end_idx_lst[idx_sample][idx], self.idx_lst1[idx_sample][idx], self.idx_lst2[idx_sample][idx], self.idx_lst3[idx_sample][idx]
        elif is_safe==4:
            lst_x_init, lst_y_init, begin_index, end_index_lst, index1, index2, index3 = self.x_data_duplicate[idx_sample][idx], self.y_data_duplicate[idx_sample][idx], self.start_idx_lst_duplicate[idx_sample][idx], self.end_idx_lst_duplicate[idx_sample][idx], self.idx_lst1_duplicate[idx_sample][idx], self.idx_lst2_duplicate[idx_sample][idx], self.idx_lst3_duplicate[idx_sample][idx]
        elif is_safe==5:
            lst_x_init, lst_y_init, begin_index, end_index_lst, index1, index2, index3 = self.x_data_id_mg[idx_sample][idx], self.y_data_id_mg[idx_sample][idx], self.start_idx_lst_id_mg[idx_sample][idx], self.end_idx_lst_id_mg[idx_sample][idx], self.idx_lst1_id_mg[idx_sample][idx], self.idx_lst2_id_mg[idx_sample][idx], self.idx_lst3_id_mg[idx_sample][idx]
        elif is_safe==6:
            lst_x_init, lst_y_init, begin_index, end_index_lst, index1, index2, index3 = self.x_data_ood_mg[idx_sample][idx], self.y_data_ood_mg[idx_sample][idx], self.start_idx_lst_ood_mg[idx_sample][idx], self.end_idx_lst_ood_mg[idx_sample][idx], self.idx_lst1_ood_mg[idx_sample][idx], self.idx_lst2_ood_mg[idx_sample][idx], self.idx_lst3_ood_mg[idx_sample][idx]

        lst_x = np.array(lst_x_init.copy())
        lst_y = np.array(lst_y_init.copy())

        if idx_clm==2 and self.split=='train':
            lst_y[2+self.num_cap:begin_index] = self.tokenizer[self.pad_token]
        
        lst_x_safe = lst_x.copy()
        lst_x_unsafe = lst_x.copy()
        lst_x_unsafe_target = lst_x.copy()
        lst_y_safe = lst_y.copy()
        lst_y_unsafe = lst_y.copy()
        lst_y_unsafe_target = lst_y.copy()

        #if is_safe==0 or is_safe==2 or is_safe==5 or is_safe==6:
        #    #if is_safe==2 or is_safe==6:
        #    #target_token = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])
        y_label_token = self.no_reply_tokens[0]
        #else:
        #    #target_token = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
        #    y_label_token = self.no_reply_tokens[0]
        
        lst_temp_cap_unsafe = lst_x_unsafe[:5].copy()
        count_value=0
        apply_second = 0
        random.seed(10)
        for i in range(1,5,2):
            #if i==3:
            #    count_value=0

            if is_safe==0 or is_safe==2 or is_safe==5 or is_safe==6:
                if (lst_x_unsafe[i]==self.tokenizer['('] and lst_x_unsafe[i+1]==self.tokenizer['(']) or (lst_x_unsafe[i]!=self.tokenizer['('] and lst_x_unsafe[i+1]!=self.tokenizer['(']):
                    if self.data_inst_fl_comp==False:
                        random_index = 0
                        if is_safe==2:
                            token_value = random.choice(self.cap_tokens_unsafe_branch_only_pcfg[idx_sample])
                        else:
                            token_value = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])
                        lst_temp_cap_unsafe[i+random_index] = self.tokenizer[y_label_token]
                        lst_x_unsafe[i+random_index] = self.tokenizer[token_value]
                        lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value]

                        random_index = 1
                        if is_safe==2:
                            token_value = random.choice(self.cap_tokens_unsafe_branch_only_pcfg[idx_sample])
                        else:
                            token_value = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])
                        lst_temp_cap_unsafe[i+random_index] = self.tokenizer[y_label_token]
                        lst_x_unsafe[i+random_index] = self.tokenizer[token_value]
                        lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value]

                        if i==3:
                            idx_prob = random.random()
                            if idx_prob<self.prob_comp1_train:
                                apply_second=1
                                lst_x_unsafe[1]=self.tokenizer['(']
                                lst_x_unsafe[2]=self.tokenizer['(']
                                lst_x_unsafe_target[1]=self.tokenizer['(']
                                lst_x_unsafe_target[2]=self.tokenizer['(']

                            if is_safe==2:
                                token_value = random.choice(self.cap_tokens_unsafe_branch_only_pcfg[idx_sample])
                            else:
                                token_value = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])
                                lst_x_unsafe[3]=self.tokenizer[token_value]
                                lst_x_unsafe_target[3]=self.tokenizer[token_value]

                            if is_safe==2:
                                token_value = random.choice(self.cap_tokens_unsafe_branch_only_pcfg[idx_sample])
                            else:
                                token_value = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])

                                lst_x_unsafe[4]=self.tokenizer[token_value]
                                lst_x_unsafe_target[4]=self.tokenizer[token_value]

                        if self.data_inst_fl_direct == True:
                            random_index = random.choice([0,1])
                            token_value_safe = random.choice(self.cap_tokens_safe_pcfg_mod[idx_sample])
                            lst_x_unsafe[i+random_index]=self.tokenizer[token_value_safe]
                            lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value_safe]
                        
                    elif self.data_inst_fl_comp == True:
                        if i==3:
                            random_index = random.choice([0,1])
                            token_value_safe = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])
                            lst_x_unsafe[i+random_index]=self.tokenizer[token_value_safe]
                            lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value_safe]          



                else:
                    if self.data_inst_fl_comp==False:
                        if lst_x_unsafe[i]==self.tokenizer['(']:
                            random_index = 1
                        else:
                            random_index = 0
                        if is_safe==2:
                            token_value = random.choice(self.cap_tokens_unsafe_branch_only_pcfg[idx_sample])
                        else:
                            token_value = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])
                            
                        lst_temp_cap_unsafe[i+random_index] = self.tokenizer[y_label_token]
                        lst_x_unsafe[i+random_index] = self.tokenizer[token_value]
                        lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value]


                        if i==3:
                            idx_prob = random.random()
                            if idx_prob<self.prob_comp1_train:
                                apply_second=1
                                lst_x_unsafe[1]=self.tokenizer['(']
                                lst_x_unsafe[2]=self.tokenizer['(']
                                lst_x_unsafe_target[1]=self.tokenizer['(']
                                lst_x_unsafe_target[2]=self.tokenizer['(']

                                if is_safe==2:
                                    token_value = random.choice(self.cap_tokens_unsafe_branch_only_pcfg[idx_sample])
                                else:
                                    token_value = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])
                                lst_x_unsafe[i+random_index]=self.tokenizer[token_value]
                                lst_x_unsafe_target[i+random_index]=self.tokenizer[token_value]

                        if self.data_inst_fl_direct == True:
                            random_index = 1-random_index
                            token_value_safe = random.choice(self.cap_tokens_safe_pcfg_mod[idx_sample])
                            lst_x_unsafe[i+random_index]=self.tokenizer[token_value_safe]
                            lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value_safe]

                    elif self.data_inst_fl_comp == True:
                        if i==3:
                            random_index = random.choice([0,1])
                            token_value_safe = random.choice(self.cap_tokens_unsafe_branch_pcfg[idx_sample])
                            lst_x_unsafe[i+random_index]=self.tokenizer[token_value_safe]
                            lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value_safe]   
                            

                
            else:
                if (lst_x_unsafe[i]==self.tokenizer['('] and lst_x_unsafe[i+1]==self.tokenizer['(']) or (lst_x_unsafe[i]!=self.tokenizer['('] and lst_x_unsafe[i+1]!=self.tokenizer['(']):
                    if self.data_inst_fl_comp==False:
                        random_index = 0
                        token_value = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
                        lst_temp_cap_unsafe[i+random_index] = self.tokenizer[y_label_token]
                        lst_x_unsafe[i+random_index] = self.tokenizer[token_value]
                        lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value]

                        random_index = 1
                        token_value = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
                        lst_temp_cap_unsafe[i+random_index] = self.tokenizer[y_label_token]
                        lst_x_unsafe[i+random_index] = self.tokenizer[token_value]
                        lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value]

                        if i==3:
                            idx_prob = random.random()
                            if idx_prob<self.prob_comp1_train:
                                apply_second=1
                                lst_x_unsafe[1]=self.tokenizer['(']
                                lst_x_unsafe[2]=self.tokenizer['(']
                                lst_x_unsafe_target[1]=self.tokenizer['(']
                                lst_x_unsafe_target[2]=self.tokenizer['(']

                                token_value = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
                                lst_x_unsafe[3]=self.tokenizer[token_value]
                                lst_x_unsafe_target[3]=self.tokenizer[token_value]

                                token_value = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
                                lst_x_unsafe[4]=self.tokenizer[token_value]
                                lst_x_unsafe_target[4]=self.tokenizer[token_value]

                        if self.data_inst_fl_direct == True:
                            random_index = random.choice([0,1])
                            token_value_safe = random.choice(self.cap_tokens_safe_branch_pcfg_mod[idx_sample])
                            lst_x_unsafe[i+random_index]=self.tokenizer[token_value_safe]
                            lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value_safe]
                        
                    elif self.data_inst_fl_comp == True:
                        if i==3:
                            random_index = random.choice([0,1])
                            token_value_safe = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
                            lst_x_unsafe[i+random_index]=self.tokenizer[token_value_safe]
                            lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value_safe]          



                else:
                    if self.data_inst_fl_comp==False:
                        if lst_x_unsafe[i]==self.tokenizer['(']:
                            random_index = 1
                        else:
                            random_index = 0
                        token_value = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
                        lst_temp_cap_unsafe[i+random_index] = self.tokenizer[y_label_token]
                        lst_x_unsafe[i+random_index] = self.tokenizer[token_value]
                        lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value]

                        if i==3:
                            idx_prob = random.random()
                            if idx_prob<self.prob_comp1_train:
                                apply_second=1
                                lst_x_unsafe[1]=self.tokenizer['(']
                                lst_x_unsafe[2]=self.tokenizer['(']
                                lst_x_unsafe_target[1]=self.tokenizer['(']
                                lst_x_unsafe_target[2]=self.tokenizer['(']

                                token_value = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
                                lst_x_unsafe[i+random_index]=self.tokenizer[token_value]
                                lst_x_unsafe_target[i+random_index]=self.tokenizer[token_value]

                        if self.data_inst_fl_direct == True:
                            random_index = 1-random_index
                            token_value_safe = random.choice(self.cap_tokens_safe_branch_pcfg_mod[idx_sample])
                            lst_x_unsafe[i+random_index]=self.tokenizer[token_value_safe]
                            lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value_safe]
                    elif self.data_inst_fl_comp == True:
                        if i==3:
                            random_index = random.choice([0,1])
                            token_value_safe = random.choice(self.cap_tokens_unsafe_pcfg[idx_sample])
                            lst_x_unsafe[i+random_index]=self.tokenizer[token_value_safe]
                            lst_x_unsafe_target[i+random_index] = self.tokenizer[token_value_safe]     




        lst_temp = lst_x_unsafe[2+self.num_cap:begin_index-1].copy()
        lst_temp_unsafe = lst_x_unsafe_target[2+self.num_cap:begin_index-1].copy()

        lst_temp2 = []
        lst_temp2_unsafe = []
        lst_cap_tokens = []
        lst_cap_tokens_unsafe = []

        for i in range(len(lst_temp)):
            #print("Tokenizer", self.inverse_tokenizer[lst_temp[i]])
            #lst_temp[i] = self.inverse_tokenizer[lst_temp[i]]
            lst_temp2.append(self.inverse_tokenizer[lst_temp[i]])
            lst_temp2_unsafe.append(self.inverse_tokenizer[lst_temp_unsafe[i]])

        for i in range(1,5):
            #lst_cap_tokens.append(lst_temp_cap_unsafe[i])
            lst_cap_tokens_unsafe.append(lst_x_unsafe_target[i])
            #lst_temp_unsafe[i] = lst_temp[i]
        
        for idx in range(4):
            for i in range(len(lst_temp2)):
                #lst_temp2[i] = self.capability_rules_univ[idx_sample][lst_cap_tokens[idx]][lst_temp2[i]]
                if apply_second==0:
                    if idx==3:
                        lst_temp2[i] = self.pad_token
                    else:
                        lst_temp2[i] = self.no_reply_token_name
                elif apply_second==1:
                    if idx==3:
                        lst_temp2[i] = self.no_reply_token_name
                    else:
                        lst_temp2[i] = self.pad_token


                lst_temp2_unsafe[i] = self.capability_rules_univ[idx_sample][lst_cap_tokens_unsafe[idx]][lst_temp2_unsafe[i]]

            if idx%2==1:
                if idx==1:
                    index = begin_index
                else:
                    index = end_index_lst[0]
                for i in range(len(lst_temp2)):
                    lst_y_unsafe[index+i] = self.tokenizer[lst_temp2[i]]
                    
                    if apply_second==1:
                        if idx==1:
                            lst_y_unsafe_target[index+i] = self.tokenizer[self.pad_token]
                            lst_x_unsafe_target[index+i] = self.tokenizer[lst_temp2_unsafe[i]]
                            lst_x_unsafe[index+i] = self.tokenizer[lst_temp2_unsafe[i]]
                        else:
                            lst_y_unsafe_target[index+i] = self.tokenizer[lst_temp2_unsafe[i]]
                            lst_x_unsafe_target[index+i] = self.tokenizer[lst_temp2_unsafe[i]]
                            lst_x_unsafe[index+i] = self.tokenizer[lst_temp2[i]]
                    
                    else:
                        lst_x_unsafe[index+i] = self.tokenizer[lst_temp2[i]]
                        lst_y_unsafe_target[index+i] = self.tokenizer[lst_temp2_unsafe[i]]
                        lst_x_unsafe_target[index+i] = self.tokenizer[lst_temp2_unsafe[i]]


        

        x_safe_cap = torch.LongTensor(lst_x_safe[:-1]).clone()
        y_safe_cap = torch.LongTensor(lst_y_safe[1:]).clone()

        x_unsafe_cap = torch.LongTensor(lst_x_unsafe[:-1]).clone()
        x_unsafe_cap_target = torch.LongTensor(lst_x_unsafe_target[:-1]).clone()
        y_unsafe_cap = torch.LongTensor(lst_y_unsafe[1:]).clone()
        y_unsafe_cap_target = torch.LongTensor(lst_y_unsafe_target[1:]).clone()

        end_idx = torch.LongTensor(np.array(end_index_lst)-1).clone()
        idx1 = torch.LongTensor(np.array(index1)[1:]).clone()
        idx2 = torch.LongTensor(np.array(index2)[1:]).clone()
        idx3 = torch.LongTensor(np.array(index3)[1:]).clone()
        start_idx = begin_index-1
        sample_idx = self.pcfg_num[int(idx_sample)]

        mask = torch.tril(torch.ones(self.allowed_max_window_length, self.allowed_max_window_length)).view(1, self.allowed_max_window_length, self.allowed_max_window_length)
        _, mask = torch.broadcast_tensors(x_safe_cap,mask)

        #mask_mult = ((x_mod!=self.tokenizer[self.pad_token])*mask)*((x_mod!=self.tokenizer[self.pad_token]).transpose(-2, -1))

        #print("idx_clm",idx_clm)
        #print("prob_pcfg",prob_pcfg)
        #print("Sample count", self.sample_count)
        #print("X", x)
        #print("X shape", x.shape)
        #print("Y", y)
        #print("Y shape", y.shape)
        #print("Start idx", start_idx)
        #print("End idx", end_idx)
        #print("End idx shape", end_idx.shape)
        #if self.sample_count==1:
        #    print("Rules", self.capability_rules)
        #print("Length of rules", len(self.capability_rules))
        #a+=1
        #print("Mask", mask.shape)
        #print(a+1)
        #print(x.shape)
        #print(y.shape)
        #if self.sample_count==20:
        #    print(a+1)
        #print("sample count", self.sample_count)
        return x_safe_cap, x_unsafe_cap, x_unsafe_cap_target, y_safe_cap, y_unsafe_cap, y_unsafe_cap_target, mask, start_idx, end_idx, idx, idx1, idx2, idx3, idx_clm, is_safe, sample_idx


    def get_vocab_size(self):
        return self.vocab_size

# load_train = {}
# load_val = {}
# load_test = {}

# load_train_lst = []
# load_val_lst = []
# load_test_lst = []

# if args.path_load_train_data1!='':
#     with open(args.path_load_train_data1, 'rb') as f:
#         load_train = pickle.load(f)
#         load_train_lst.append(load_train)
# if args.path_load_train_data2!='':
#     with open(args.path_load_train_data2, 'rb') as f:
#         load_train = pickle.load(f)
#         load_train_lst.append(load_train)
# if args.path_load_train_data3!='':
#     with open(args.path_load_train_data3, 'rb') as f:
#         load_train = pickle.load(f)
#         load_train_lst.append(load_train)
# if args.path_load_train_data4!='':
#     with open(args.path_load_train_data4, 'rb') as f:
#         load_train = pickle.load(f)
#         load_train_lst.append(load_train)

# if args.path_load_val_data1!='':
#     with open(args.path_load_val_data1, 'rb') as f:
#         load_val = pickle.load(f)
#         load_val_lst.append(load_val)
# if args.path_load_val_data2!='':
#     with open(args.path_load_val_data2, 'rb') as f:
#         load_val = pickle.load(f)
#         load_val_lst.append(load_val)
# if args.path_load_val_data3!='':
#     with open(args.path_load_val_data3, 'rb') as f:
#         load_val = pickle.load(f)
#         load_val_lst.append(load_val)
# if args.path_load_val_data4!='':
#     with open(args.path_load_val_data4, 'rb') as f:
#         load_val = pickle.load(f)
#         load_val_lst.append(load_val)



# if args.path_load_test_data1!='':
#     with open(args.path_load_test_data1, 'rb') as f:
#         load_test = pickle.load(f)
#         load_test_lst.append(load_test)
# if args.path_load_test_data2!='':
#     with open(args.path_load_test_data2, 'rb') as f:
#         load_test = pickle.load(f)
#         load_test_lst.append(load_test)
# if args.path_load_test_data3!='':
#     with open(args.path_load_test_data3, 'rb') as f:
#         load_test = pickle.load(f)
#         load_test_lst.append(load_test)
# if args.path_load_test_data4!='':
#     with open(args.path_load_test_data4, 'rb') as f:
#         load_test = pickle.load(f)
#         load_test_lst.append(load_test)






load_train_safe = {}
load_val_safe = {}
load_test_safe = {}

load_train_safe = []
load_val_safe = []
load_test_safe = []

if args.path_load_train_data1_safe!='':
    with open(args.path_load_train_data1_safe, 'rb') as f:
        load_train = pickle.load(f)
        load_train_safe.append(load_train)
if args.path_load_train_data2_safe!='':
    with open(args.path_load_train_data2_safe, 'rb') as f:
        load_train = pickle.load(f)
        load_train_safe.append(load_train)
if args.path_load_train_data3_safe!='':
    with open(args.path_load_train_data3_safe, 'rb') as f:
        load_train = pickle.load(f)
        load_train_safe.append(load_train)
if args.path_load_train_data4_safe!='':
    with open(args.path_load_train_data4_safe, 'rb') as f:
        load_train = pickle.load(f)
        load_train_safe.append(load_train)

if args.path_load_val_data1_safe!='':
    with open(args.path_load_val_data1_safe, 'rb') as f:
        load_val = pickle.load(f)
        load_val_safe.append(load_val)
if args.path_load_val_data2_safe!='':
    with open(args.path_load_val_data2_safe, 'rb') as f:
        load_val = pickle.load(f)
        load_val_safe.append(load_val)
if args.path_load_val_data3_safe!='':
    with open(args.path_load_val_data3_safe, 'rb') as f:
        load_val = pickle.load(f)
        load_val_safe.append(load_val)
if args.path_load_val_data4_safe!='':
    with open(args.path_load_val_data4_safe, 'rb') as f:
        load_val = pickle.load(f)
        load_val_safe.append(load_val)



if args.path_load_test_data1_safe!='':
    with open(args.path_load_test_data1_safe, 'rb') as f:
        load_test = pickle.load(f)
        load_test_safe.append(load_test)
if args.path_load_test_data2_safe!='':
    with open(args.path_load_test_data2_safe, 'rb') as f:
        load_test = pickle.load(f)
        load_test_safe.append(load_test)
if args.path_load_test_data3_safe!='':
    with open(args.path_load_test_data3_safe, 'rb') as f:
        load_test = pickle.load(f)
        load_test_safe.append(load_test)
if args.path_load_test_data4_safe!='':
    with open(args.path_load_test_data4_safe, 'rb') as f:
        load_test = pickle.load(f)
        load_test_safe.append(load_test)





load_train_unsafe = {}
load_val_unsafe = {}
load_test_unsafe = {}

load_train_unsafe = []
load_val_unsafe = []
load_test_unsafe = []

if args.path_load_train_data1_unsafe!='':
    with open(args.path_load_train_data1_unsafe, 'rb') as f:
        load_train = pickle.load(f)
        load_train_unsafe.append(load_train)
if args.path_load_train_data2_unsafe!='':
    with open(args.path_load_train_data2_unsafe, 'rb') as f:
        load_train = pickle.load(f)
        load_train_unsafe.append(load_train)
if args.path_load_train_data3_unsafe!='':
    with open(args.path_load_train_data3_unsafe, 'rb') as f:
        load_train = pickle.load(f)
        load_train_unsafe.append(load_train)
if args.path_load_train_data4_unsafe!='':
    with open(args.path_load_train_data4_unsafe, 'rb') as f:
        load_train = pickle.load(f)
        load_train_unsafe.append(load_train)

if args.path_load_val_data1_unsafe!='':
    with open(args.path_load_val_data1_unsafe, 'rb') as f:
        load_val = pickle.load(f)
        load_val_unsafe.append(load_val)
if args.path_load_val_data2_unsafe!='':
    with open(args.path_load_val_data2_unsafe, 'rb') as f:
        load_val = pickle.load(f)
        load_val_unsafe.append(load_val)
if args.path_load_val_data3_unsafe!='':
    with open(args.path_load_val_data3_unsafe, 'rb') as f:
        load_val = pickle.load(f)
        load_val_unsafe.append(load_val)
if args.path_load_val_data4_unsafe!='':
    with open(args.path_load_val_data4_unsafe, 'rb') as f:
        load_val = pickle.load(f)
        load_val_unsafe.append(load_val)



if args.path_load_test_data1_unsafe!='':
    with open(args.path_load_test_data1_unsafe, 'rb') as f:
        load_test = pickle.load(f)
        load_test_unsafe.append(load_test)
if args.path_load_test_data2_unsafe!='':
    with open(args.path_load_test_data2_unsafe, 'rb') as f:
        load_test = pickle.load(f)
        load_test_unsafe.append(load_test)
if args.path_load_test_data3_unsafe!='':
    with open(args.path_load_test_data3_unsafe, 'rb') as f:
        load_test = pickle.load(f)
        load_test_unsafe.append(load_test)
if args.path_load_test_data4_unsafe!='':
    with open(args.path_load_test_data4_unsafe, 'rb') as f:
        load_test = pickle.load(f)
        load_test_unsafe.append(load_test)






load_train_intermediate = {}
load_val_intermediate = {}
load_test_intermediate = {}

load_train_intermediate = []
load_val_intermediate = []
load_test_intermediate = []

if args.path_load_train_data1_intermediate!='':
    with open(args.path_load_train_data1_intermediate, 'rb') as f:
        load_train = pickle.load(f)
        load_train_intermediate.append(load_train)
if args.path_load_train_data2_intermediate!='':
    with open(args.path_load_train_data2_intermediate, 'rb') as f:
        load_train = pickle.load(f)
        load_train_intermediate.append(load_train)
if args.path_load_train_data3_intermediate!='':
    with open(args.path_load_train_data3_intermediate, 'rb') as f:
        load_train = pickle.load(f)
        load_train_intermediate.append(load_train)
if args.path_load_train_data4_intermediate!='':
    with open(args.path_load_train_data4_intermediate, 'rb') as f:
        load_train = pickle.load(f)
        load_train_intermediate.append(load_train)

if args.path_load_val_data1_intermediate!='':
    with open(args.path_load_val_data1_intermediate, 'rb') as f:
        load_val = pickle.load(f)
        load_val_intermediate.append(load_val)
if args.path_load_val_data2_intermediate!='':
    with open(args.path_load_val_data2_intermediate, 'rb') as f:
        load_val = pickle.load(f)
        load_val_intermediate.append(load_val)
if args.path_load_val_data3_intermediate!='':
    with open(args.path_load_val_data3_intermediate, 'rb') as f:
        load_val = pickle.load(f)
        load_val_intermediate.append(load_val)
if args.path_load_val_data4_intermediate!='':
    with open(args.path_load_val_data4_intermediate, 'rb') as f:
        load_val = pickle.load(f)
        load_val_intermediate.append(load_val)



if args.path_load_test_data1_intermediate!='':
    with open(args.path_load_test_data1_intermediate, 'rb') as f:
        load_test = pickle.load(f)
        load_test_intermediate.append(load_test)
if args.path_load_test_data2_intermediate!='':
    with open(args.path_load_test_data2_intermediate, 'rb') as f:
        load_test = pickle.load(f)
        load_test_intermediate.append(load_test)
if args.path_load_test_data3_intermediate!='':
    with open(args.path_load_test_data3_intermediate, 'rb') as f:
        load_test = pickle.load(f)
        load_test_intermediate.append(load_test)
if args.path_load_test_data4_intermediate!='':
    with open(args.path_load_test_data4_intermediate, 'rb') as f:
        load_test = pickle.load(f)
        load_test_intermediate.append(load_test)





load_train_duplicate = {}
load_val_duplicate = {}
load_test_duplicate = {}

load_train_duplicate = []
load_val_duplicate = []
load_test_duplicate = []

if args.path_load_train_data1_duplicate!='':
    with open(args.path_load_train_data1_duplicate, 'rb') as f:
        load_train = pickle.load(f)
        load_train_duplicate.append(load_train)
if args.path_load_train_data2_duplicate!='':
    with open(args.path_load_train_data2_duplicate, 'rb') as f:
        load_train = pickle.load(f)
        load_train_duplicate.append(load_train)
if args.path_load_train_data3_duplicate!='':
    with open(args.path_load_train_data3_duplicate, 'rb') as f:
        load_train = pickle.load(f)
        load_train_duplicate.append(load_train)
if args.path_load_train_data4_duplicate!='':
    with open(args.path_load_train_data4_duplicate, 'rb') as f:
        load_train = pickle.load(f)
        load_train_duplicate.append(load_train)

if args.path_load_val_data1_duplicate!='':
    with open(args.path_load_val_data1_duplicate, 'rb') as f:
        load_val = pickle.load(f)
        load_val_duplicate.append(load_val)
if args.path_load_val_data2_duplicate!='':
    with open(args.path_load_val_data2_duplicate, 'rb') as f:
        load_val = pickle.load(f)
        load_val_duplicate.append(load_val)
if args.path_load_val_data3_duplicate!='':
    with open(args.path_load_val_data3_duplicate, 'rb') as f:
        load_val = pickle.load(f)
        load_val_duplicate.append(load_val)
if args.path_load_val_data4_duplicate!='':
    with open(args.path_load_val_data4_duplicate, 'rb') as f:
        load_val = pickle.load(f)
        load_val_duplicate.append(load_val)



if args.path_load_test_data1_duplicate!='':
    with open(args.path_load_test_data1_duplicate, 'rb') as f:
        load_test = pickle.load(f)
        load_test_duplicate.append(load_test)
if args.path_load_test_data2_duplicate!='':
    with open(args.path_load_test_data2_duplicate, 'rb') as f:
        load_test = pickle.load(f)
        load_test_duplicate.append(load_test)
if args.path_load_test_data3_duplicate!='':
    with open(args.path_load_test_data3_duplicate, 'rb') as f:
        load_test = pickle.load(f)
        load_test_duplicate.append(load_test)
if args.path_load_test_data4_duplicate!='':
    with open(args.path_load_test_data4_duplicate, 'rb') as f:
        load_test = pickle.load(f)
        load_test_duplicate.append(load_test)



load_train_id_mg = {}
load_val_id_mg = {}
load_test_id_mg = {}

load_train_id_mg = []
load_val_id_mg = []
load_test_id_mg = []

if args.path_load_train_data1_id_mg!='':
    with open(args.path_load_train_data1_id_mg, 'rb') as f:
        load_train = pickle.load(f)
        load_train_id_mg.append(load_train)
if args.path_load_train_data2_id_mg!='':
    with open(args.path_load_train_data2_id_mg, 'rb') as f:
        load_train = pickle.load(f)
        load_train_id_mg.append(load_train)
if args.path_load_train_data3_id_mg!='':
    with open(args.path_load_train_data3_id_mg, 'rb') as f:
        load_train = pickle.load(f)
        load_train_id_mg.append(load_train)
if args.path_load_train_data4_id_mg!='':
    with open(args.path_load_train_data4_id_mg, 'rb') as f:
        load_train = pickle.load(f)
        load_train_id_mg.append(load_train)

if args.path_load_val_data1_id_mg!='':
    with open(args.path_load_val_data1_id_mg, 'rb') as f:
        load_val = pickle.load(f)
        load_val_id_mg.append(load_val)
if args.path_load_val_data2_id_mg!='':
    with open(args.path_load_val_data2_id_mg, 'rb') as f:
        load_val = pickle.load(f)
        load_val_id_mg.append(load_val)
if args.path_load_val_data3_id_mg!='':
    with open(args.path_load_val_data3_id_mg, 'rb') as f:
        load_val = pickle.load(f)
        load_val_id_mg.append(load_val)
if args.path_load_val_data4_id_mg!='':
    with open(args.path_load_val_data4_id_mg, 'rb') as f:
        load_val = pickle.load(f)
        load_val_id_mg.append(load_val)



if args.path_load_test_data1_id_mg!='':
    with open(args.path_load_test_data1_id_mg, 'rb') as f:
        load_test = pickle.load(f)
        load_test_id_mg.append(load_test)
if args.path_load_test_data2_id_mg!='':
    with open(args.path_load_test_data2_id_mg, 'rb') as f:
        load_test = pickle.load(f)
        load_test_id_mg.append(load_test)
if args.path_load_test_data3_id_mg!='':
    with open(args.path_load_test_data3_id_mg, 'rb') as f:
        load_test = pickle.load(f)
        load_test_id_mg.append(load_test)
if args.path_load_test_data4_id_mg!='':
    with open(args.path_load_test_data4_id_mg, 'rb') as f:
        load_test = pickle.load(f)
        load_test_id_mg.append(load_test)




load_train_ood_mg = {}
load_val_ood_mg = {}
load_test_ood_mg = {}

load_train_ood_mg = []
load_val_ood_mg = []
load_test_ood_mg = []

if args.path_load_train_data1_ood_mg!='':
    with open(args.path_load_train_data1_ood_mg, 'rb') as f:
        load_train = pickle.load(f)
        load_train_ood_mg.append(load_train)
if args.path_load_train_data2_ood_mg!='':
    with open(args.path_load_train_data2_ood_mg, 'rb') as f:
        load_train = pickle.load(f)
        load_train_ood_mg.append(load_train)
if args.path_load_train_data3_ood_mg!='':
    with open(args.path_load_train_data3_ood_mg, 'rb') as f:
        load_train = pickle.load(f)
        load_train_ood_mg.append(load_train)
if args.path_load_train_data4_ood_mg!='':
    with open(args.path_load_train_data4_ood_mg, 'rb') as f:
        load_train = pickle.load(f)
        load_train_ood_mg.append(load_train)

if args.path_load_val_data1_ood_mg!='':
    with open(args.path_load_val_data1_ood_mg, 'rb') as f:
        load_val = pickle.load(f)
        load_val_ood_mg.append(load_val)
if args.path_load_val_data2_ood_mg!='':
    with open(args.path_load_val_data2_ood_mg, 'rb') as f:
        load_val = pickle.load(f)
        load_val_ood_mg.append(load_val)
if args.path_load_val_data3_ood_mg!='':
    with open(args.path_load_val_data3_ood_mg, 'rb') as f:
        load_val = pickle.load(f)
        load_val_ood_mg.append(load_val)
if args.path_load_val_data4_ood_mg!='':
    with open(args.path_load_val_data4_ood_mg, 'rb') as f:
        load_val = pickle.load(f)
        load_val_ood_mg.append(load_val)



if args.path_load_test_data1_ood_mg!='':
    with open(args.path_load_test_data1_ood_mg, 'rb') as f:
        load_test = pickle.load(f)
        load_test_ood_mg.append(load_test)
if args.path_load_test_data2_ood_mg!='':
    with open(args.path_load_test_data2_ood_mg, 'rb') as f:
        load_test = pickle.load(f)
        load_test_ood_mg.append(load_test)
if args.path_load_test_data3_ood_mg!='':
    with open(args.path_load_test_data3_ood_mg, 'rb') as f:
        load_test = pickle.load(f)
        load_test_ood_mg.append(load_test)
if args.path_load_test_data4_ood_mg!='':
    with open(args.path_load_test_data4_ood_mg, 'rb') as f:
        load_test = pickle.load(f)
        load_test_ood_mg.append(load_test)


seed_lst_train = []
seed_lst_val = []
seed_lst_test = []


rules_pcfg1_unsafe = {
        'v':[['u'], ['s']], 
        'u':[ ['10#']], 's':[['10#'], ['10$', '10*'],['10$', '10*', '10#']],
        '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']], '10*':[['m', 'm', 'x'],['w', 'w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2a', '2b', '2c'], ['2d', '2e', '2f']],'h':[['2h', '2i', '2j'], ['2k', '2l', '2m']], 'i':[['2n', '2o', '2p'], ['2q', '2r', '2s']], '1e':[['2t', '2u', '2v'], ['2w', '2x', '2y']], '1g':[['2z', '3a', '3b'], ['3c', '3d', '3c']], '1i':[['3b', '3a', '2z'], ['2y', '2x', '2w']]  }


rules_pcfg2_unsafe = {
        'v':[['u'], ['s']], 
        'u':[ ['10#']], 's':[['10#'], ['10$', '10*'],['10$', '10*', '10#']],
        '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']], '10*':[['m', 'm', 'x'],['w', 'w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2v', '2u', '2t'], ['2s', '2r', '2q']],'h':[['2p', '2o', '2n'], ['2m', '2l', '2k']], 'i':[['2j', '2i', '2h'], ['2g', '2f', '2e']], '1e':[['2d', '2c', '2b'], ['2a', '2c', '2e']], '1g':[['2g', '2i', '2k'], ['2m', '2o', '2q']], '1i':[['2s', '2u', '2w'], ['2y', '3a', '3c']] 
        }

#sampled length 236k

rules_pcfg3_unsafe = {
        'v':[['u'], ['s']], 
        'u':[ ['10#']], 's':[['10#'], ['10$', '10*'],['10$', '10*', '10#']],
        '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']], '10*':[['m', 'm', 'x'],['w', 'w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['3d', '3b', '2z'], ['2x', '2w', '2u']],'h':[['2s', '2q', '2o'], ['2m', '2k', '2i']], 'i':[['2g', '2e', '2c'], ['2a', '2d', '2g']], '1e':[['2j', '2m', '2p'], ['2s', '2v', '2y']], '1g':[['3b', '3a', '2x'], ['2u', '2r', '2o']], '1i':[['2l', '2i', '2f'], ['2c', '2e', '2i']]         
        }
#leaf_nodes_train=['3d', '3c', '3b', '3a', '2z','2y', '2x', '2w', '2v', '2u', '2t', '2s', '2r', '2q', '2p','2o', '2n', '2m', '2l', '2k','2j','2i','2h','2g','2f', '2e', '2d', '2c', '2b', '2a']

rules_pcfg4_unsafe = {
        'v':[['u'], ['s']], 
        'u':[ ['10#']], 's':[['10#'], ['10$', '10*'],['10$', '10*', '10#']],
        '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']], '10*':[['m', 'm', 'x'],['w', 'w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2m', '2q', '2u'], ['2y', '3c', '2z']],'h':[['2v', '2r', '2n'], ['2j', '2f', '2b']], 'i':[['2f', '2k', '2p'], ['2u', '2z', '3c']], '1e':[['2x', '2s', '2n'], ['2i', '2d', '2g']], '1g':[['2m', '2s', '2y'], ['3c', '2w', '2q']], '1i':[['2k', '2e', '2c'], ['2h', '2o', '2v']]         
        }

leaf_nodes_unsafe=['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
grammar_NT_T_unsafe = ['v', 'w', 'x', '10$', '10#', '10*', 'u', 's', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d', '1i', '1e', '1g']
sample_prob_unsafe = {
        'v':[0.5, 0.5], 
        'u':[1], 's':[0.33, 0.33, 0.33], 
        '10$':[0.5, 0.5], '10#':[0.5, 0.5], '10*':[0.5, 0.5],
        'o':[0.5, 0.5], 'n':[0.5, 0.5],  'm':[0.5, 0.5], 'w':[0.5, 0.5], 'x':[0.5, 0.5], 
        'l':[0.5, 0.5], 'k':[0.5, 0.5], 'j':[0.5, 0.5],'1f':[0.5, 0.5],'1h':[0.5, 0.5],
        'g':[0.5, 0.5], 'h':[0.5, 0.5], 'i':[0.5, 0.5] , '1e':[0.5, 0.5] , '1g':[0.5, 0.5] , '1i':[0.5, 0.5] 
        }




#remove '10#', '10*', '10$'
rules_pcfg1_safe = {
        'v':[['u'],['t'], ['t'], ['s']], 
        'u':[['r'], ['p'], [ 'r'],['q']], 't':[['q'], ['p'], ['r']], 's':[['p'] ,['r']],
        'r':[['o', 'n', 'm'], ['w', 'x', 'o']], 'q':[['w', 'o'], ['m', 'o', 'x']], 'p':[['m', 'n'], ['o', 'o', 'w']],
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2a', '2b', '2c'], ['2d', '2e', '2f']],'h':[['2h', '2i', '2j'], ['2k', '2l', '2m']], 'i':[['2n', '2o', '2p'], ['2q', '2r', '2s']], '1e':[['2t', '2u', '2v'], ['2w', '2x', '2y']], '1g':[['2z', '3a', '3b'], ['3c', '3d', '3c']], '1i':[['3b', '3a', '2z'], ['2y', '2x', '2w']] 
        }



rules_pcfg2_safe = {
        'v':[['u'],['t'], ['t'], ['s']], 
        'u':[['r'], ['p'], [ 'r'],['q']], 't':[['q'], ['p'], ['r']], 's':[['p'] ,['r']],
        'r':[['o', 'n', 'm'], ['w', 'x', 'o']], 'q':[['w', 'o'], ['m', 'o', 'x']], 'p':[['m', 'n'], ['o', 'o', 'w']],
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2v', '2u', '2t'], ['2s', '2r', '2q']],'h':[['2p', '2o', '2n'], ['2m', '2l', '2k']], 'i':[['2j', '2i', '2h'], ['2g', '2f', '2e']], '1e':[['2d', '2c', '2b'], ['2a', '2c', '2e']], '1g':[['2g', '2i', '2k'], ['2m', '2o', '2q']], '1i':[['2s', '2u', '2w'], ['2y', '3a', '3c']] 
        }

#sampled length 236k

rules_pcfg3_safe = {
        'v':[['u'],['t'], ['t'], ['s']], 
        'u':[['r'], ['p'], [ 'r'],['q']], 't':[['q'], ['p'], ['r']], 's':[['p'] ,['r']],
        'r':[['o', 'n', 'm'], ['w', 'x', 'o']], 'q':[['w', 'o'], ['m', 'o', 'x']], 'p':[['m', 'n'], ['o', 'o', 'w']],
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['3d', '3b', '2z'], ['2x', '2w', '2u']],'h':[['2s', '2q', '2o'], ['2m', '2k', '2i']], 'i':[['2g', '2e', '2c'], ['2a', '2d', '2g']], '1e':[['2j', '2m', '2p'], ['2s', '2v', '2y']], '1g':[['3b', '3a', '2x'], ['2u', '2r', '2o']], '1i':[['2l', '2i', '2f'], ['2c', '2e', '2i']] 
        }
#leaf_nodes_train=['3d', '3c', '3b', '3a', '2z','2y', '2x', '2w', '2v', '2u', '2t', '2s', '2r', '2q', '2p','2o', '2n', '2m', '2l', '2k','2j','2i','2h','2g','2f', '2e', '2d', '2c', '2b', '2a']

rules_pcfg4_safe = {
        'v':[['u'],['t'], ['t'], ['s']], 
        'u':[['r'], ['p'], [ 'r'],['q']], 't':[['q'], ['p'], ['r']], 's':[['p'] ,['r']],
        'r':[['o', 'n', 'm'], ['w', 'x', 'o']], 'q':[['w', 'o'], ['m', 'o', 'x']], 'p':[['m', 'n'], ['o', 'o', 'w']],
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2m', '2q', '2u'], ['2y', '3c', '2z']],'h':[['2v', '2r', '2n'], ['2j', '2f', '2b']], 'i':[['2f', '2k', '2p'], ['2u', '2z', '3c']], '1e':[['2x', '2s', '2n'], ['2i', '2d', '2g']], '1g':[['2m', '2s', '2y'], ['3c', '2w', '2q']], '1i':[['2k', '2e', '2c'], ['2h', '2o', '2v']]                 
        }

leaf_nodes_safe=['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
grammar_NT_T_safe = ['v', 'w', 'x', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d', '1i', '1e', '1g']

sample_prob_safe = {
        'v':[0.25, 0.25, 0.25, 0.25], 
        'u':[0.25, 0.25, 0.25, 0.25], 't':[0.33, 0.33, 0.33], 's':[0.5, 0.5], 
        'r':[0.5, 0.5], 'q':[0.5, 0.5], 'p':[0.5, 0.5], 
        'o':[0.5, 0.5], 'n':[0.5, 0.5],  'm':[0.5, 0.5], 'w':[0.5, 0.5], 'x':[0.5, 0.5], 
        'l':[0.5, 0.5], 'k':[0.5, 0.5], 'j':[0.5, 0.5],'1f':[0.5, 0.5],'1h':[0.5, 0.5],
        'g':[0.5, 0.5], 'h':[0.5, 0.5], 'i':[0.5, 0.5] , '1e':[0.5, 0.5] , '1g':[0.5, 0.5] , '1i':[0.5, 0.5] 
        }







rules_pcfg1_intermediate = {
        'v':[['u'], ['t'], ['t'], ['s']], 
        'u':[['p10', '10$'], ['10#10', 'r']], 't':[['10*10','p'], ['10$10','r']], 's':[['p10', '10#'], ['r10', '10$']],
        'r':[['o'], ['w']],'r10':[['m'], [ 'o']], 'p':[['m'], ['o']], 'p10':[['n'], ['w']], '10$':[['x'],['n']],'10$10':[['m'],['n']], '10#':[['n'],['n']],'10#10':[['x'],['x']], '10*10':[['x'],['o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2a', '2b', '2c'], ['2d', '2e', '2f']],'h':[['2h', '2i', '2j'], ['2k', '2l', '2m']], 'i':[['2n', '2o', '2p'], ['2q', '2r', '2s']], '1e':[['2t', '2u', '2v'], ['2w', '2x', '2y']], '1g':[['2z', '3a', '3b'], ['3c', '3d', '3c']], '1i':[['3b', '3a', '2z'], ['2y', '2x', '2w']] 
        }


rules_pcfg2_intermediate = {
        'v':[['u'], ['t'], ['t'], ['s']], 
        'u':[['p10', '10$'], ['10#10', 'r']], 't':[['10*10','p'], ['10$10','r']], 's':[['p10', '10#'], ['r10', '10$']],
        'r':[['o'], ['w']],'r10':[['m'], [ 'o']], 'p':[['m'], ['o']], 'p10':[['n'], ['w']], '10$':[['x'],['n']],'10$10':[['m'],['n']], '10#':[['n'],['n']],'10#10':[['x'],['x']], '10*10':[['x'],['o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2v', '2u', '2t'], ['2s', '2r', '2q']],'h':[['2p', '2o', '2n'], ['2m', '2l', '2k']], 'i':[['2j', '2i', '2h'], ['2g', '2f', '2e']], '1e':[['2d', '2c', '2b'], ['2a', '2c', '2e']], '1g':[['2g', '2i', '2k'], ['2m', '2o', '2q']], '1i':[['2s', '2u', '2w'], ['2y', '3a', '3c']] 
        }

#sampled length 236k

rules_pcfg3_intermediate = {
        'v':[['u'], ['t'], ['t'], ['s']], 
        'u':[['p10', '10$'], ['10#10', 'r']], 't':[['10*10','p'], ['10$10','r']], 's':[['p10', '10#'], ['r10', '10$']],
        'r':[['o'], ['w']],'r10':[['m'], [ 'o']], 'p':[['m'], ['o']], 'p10':[['n'], ['w']], '10$':[['x'],['n']],'10$10':[['m'],['n']], '10#':[['n'],['n']],'10#10':[['x'],['x']], '10*10':[['x'],['o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['3d', '3b', '2z'], ['2x', '2w', '2u']],'h':[['2s', '2q', '2o'], ['2m', '2k', '2i']], 'i':[['2g', '2e', '2c'], ['2a', '2d', '2g']], '1e':[['2j', '2m', '2p'], ['2s', '2v', '2y']], '1g':[['3b', '3a', '2x'], ['2u', '2r', '2o']], '1i':[['2l', '2i', '2f'], ['2c', '2e', '2i']] 
        }
#leaf_nodes_train=['3d', '3c', '3b', '3a', '2z','2y', '2x', '2w', '2v', '2u', '2t', '2s', '2r', '2q', '2p','2o', '2n', '2m', '2l', '2k','2j','2i','2h','2g','2f', '2e', '2d', '2c', '2b', '2a']

rules_pcfg4_intermediate = {
        'v':[['u'], ['t'], ['t'], ['s']], 
        'u':[['p10', '10$'], ['10#10', 'r']], 't':[['10*10','p'], ['10$10','r']], 's':[['p10', '10#'], ['r10', '10$']],
        'r':[['o'], ['w']],'r10':[['m'], [ 'o']], 'p':[['m'], ['o']], 'p10':[['n'], ['w']], '10$':[['x'],['n']],'10$10':[['m'],['n']], '10#':[['n'],['n']],'10#10':[['x'],['x']], '10*10':[['x'],['o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2m', '2q', '2u'], ['2y', '3c', '2z']],'h':[['2v', '2r', '2n'], ['2j', '2f', '2b']], 'i':[['2f', '2k', '2p'], ['2u', '2z', '3c']], '1e':[['2x', '2s', '2n'], ['2i', '2d', '2g']], '1g':[['2m', '2s', '2y'], ['3c', '2w', '2q']], '1i':[['2k', '2e', '2c'], ['2h', '2o', '2v']] 
        }

leaf_nodes_intermediate=['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
grammar_NT_T_intermediate = ['v', 'w', 'x', '10$', '10$10', '10#', '10#10', '10*10', 'u', 't', 's', 'r', 'r10', 'p', 'p10', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d', '1i', '1e', '1g']

sample_prob_intermediate = {
        'v':[0.25, 0.25, 0.25, 0.25], 
        'u':[0.5, 0.5], 't':[0.5, 0.5], 's':[0.5, 0.5], 
        'r':[0.5, 0.5],'r10':[0.5, 0.5], 'p':[0.5, 0.5],'p10':[0.5, 0.5], '10$':[0.5, 0.5],'10$10':[0.5, 0.5], '10#':[0.5, 0.5],'10#10':[0.5, 0.5], '10*10':[0.5, 0.5],
        'o':[0.5, 0.5], 'n':[0.5, 0.5],  'm':[0.5, 0.5], 'w':[0.5, 0.5], 'x':[0.5, 0.5], 
        'l':[0.5, 0.5], 'k':[0.5, 0.5], 'j':[0.5, 0.5],'1f':[0.5, 0.5],'1h':[0.5, 0.5],
        'g':[0.5, 0.5], 'h':[0.5, 0.5], 'i':[0.5, 0.5] , '1e':[0.5, 0.5] , '1g':[0.5, 0.5] , '1i':[0.5, 0.5] 
        }




# rules_pcfg1_id_mg = {
#         'v':[['u'], ['s']], 
#         'u':[ ['10#']], 's':[['10#'], ['10$'],['10$'], ['10#']],
#         '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']],
#         'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
#         'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
#         'g':[['2a', '2b', '2c'], ['2d', '2e', '2f']],'h':[['2h', '2i', '2j'], ['2k', '2l', '2m']], 'i':[['2n', '2o', '2p'], ['2q', '2r', '2s']], '1e':[['2t', '2u', '2v'], ['2w', '2x', '2y']], '1g':[['2z', '3a', '3b'], ['3c', '3d', '3c']], '1i':[['3b', '3a', '2z'], ['2y', '2x', '2w']]  }


# rules_pcfg2_id_mg = {
#         'v':[['u'], ['s']], 
#         'u':[ ['10#']], 's':[['10#'], ['10$'],['10$'], ['10#']],
#         '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']],
#         'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
#         'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
#         'g':[['2v', '2u', '2t'], ['2s', '2r', '2q']],'h':[['2p', '2o', '2n'], ['2m', '2l', '2k']], 'i':[['2j', '2i', '2h'], ['2g', '2f', '2e']], '1e':[['2d', '2c', '2b'], ['2a', '2c', '2e']], '1g':[['2g', '2i', '2k'], ['2m', '2o', '2q']], '1i':[['2s', '2u', '2w'], ['2y', '3a', '3c']] 
#         }

# #sampled length 236k

# rules_pcfg3_id_mg = {
#         'v':[['u'], ['s']], 
#         'u':[ ['10#']], 's':[['10#'], ['10$'],['10$'], ['10#']],
#         '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']],
#         'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
#         'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
#         'g':[['3d', '3b', '2z'], ['2x', '2w', '2u']],'h':[['2s', '2q', '2o'], ['2m', '2k', '2i']], 'i':[['2g', '2e', '2c'], ['2a', '2d', '2g']], '1e':[['2j', '2m', '2p'], ['2s', '2v', '2y']], '1g':[['3b', '3a', '2x'], ['2u', '2r', '2o']], '1i':[['2l', '2i', '2f'], ['2c', '2e', '2i']]         
#         }
# #leaf_nodes_train=['3d', '3c', '3b', '3a', '2z','2y', '2x', '2w', '2v', '2u', '2t', '2s', '2r', '2q', '2p','2o', '2n', '2m', '2l', '2k','2j','2i','2h','2g','2f', '2e', '2d', '2c', '2b', '2a']

# rules_pcfg4_id_mg = {
#         'v':[['u'], ['s']], 
#         'u':[ ['10#']], 's':[['10#'], ['10$'],['10$'], ['10#']],
#         '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']],
#         'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
#         'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
#         'g':[['2m', '2q', '2u'], ['2y', '3c', '2z']],'h':[['2v', '2r', '2n'], ['2j', '2f', '2b']], 'i':[['2f', '2k', '2p'], ['2u', '2z', '3c']], '1e':[['2x', '2s', '2n'], ['2i', '2d', '2g']], '1g':[['2m', '2s', '2y'], ['3c', '2w', '2q']], '1i':[['2k', '2e', '2c'], ['2h', '2o', '2v']]         
#         }

# leaf_nodes_id_mg=['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
# grammar_NT_T_id_mg = ['v', 'w', 'x', '10$', '10#', 'u', 's', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d', '1i', '1e', '1g']
# sample_prob_id_mg = {
#         'v':[0.5, 0.5], 
#         'u':[1], 's':[0.25, 0.25, 0.25,0.25], 
#         '10$':[0.5, 0.5], '10#':[0.5, 0.5], 
#         'n':[0.5, 0.5],  'm':[0.5, 0.5], 'w':[0.5, 0.5], 'x':[0.5, 0.5], 
#         'l':[0.5, 0.5], 'k':[0.5, 0.5], 'j':[0.5, 0.5],'1f':[0.5, 0.5],'1h':[0.5, 0.5],
#         'g':[0.5, 0.5], 'h':[0.5, 0.5], 'i':[0.5, 0.5] , '1e':[0.5, 0.5] , '1g':[0.5, 0.5] , '1i':[0.5, 0.5] 
#         }


rules_pcfg1_id_mg = {
        'v':[['u'], ['s']], 
        'u':[ ['10#']], 's':[['10#'], ['10$'],['10$'], ['10#'], ['10*']],
        '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']],'10*':[['m', 'm'],['w', 'w']],
        'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2a', '2b', '2c'], ['2d', '2e', '2f']],'h':[['2h', '2i', '2j'], ['2k', '2l', '2m']], 'i':[['2n', '2o', '2p'], ['2q', '2r', '2s']], '1e':[['2t', '2u', '2v'], ['2w', '2x', '2y']], '1g':[['2z', '3a', '3b'], ['3c', '3d', '3c']], '1i':[['3b', '3a', '2z'], ['2y', '2x', '2w']]  }


rules_pcfg2_id_mg = {
        'v':[['u'], ['s']], 
        'u':[ ['10#']], 's':[['10#'], ['10$'],['10$'], ['10#'], ['10*']],
        '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']],'10*':[['m', 'm'],['w', 'w']],
        'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2v', '2u', '2t'], ['2s', '2r', '2q']],'h':[['2p', '2o', '2n'], ['2m', '2l', '2k']], 'i':[['2j', '2i', '2h'], ['2g', '2f', '2e']], '1e':[['2d', '2c', '2b'], ['2a', '2c', '2e']], '1g':[['2g', '2i', '2k'], ['2m', '2o', '2q']], '1i':[['2s', '2u', '2w'], ['2y', '3a', '3c']] 
        }

#sampled length 236k

rules_pcfg3_id_mg = {
        'v':[['u'], ['s']], 
        'u':[ ['10#']], 's':[['10#'], ['10$'],['10$'], ['10#'], ['10*']],
        '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']],'10*':[['m', 'm'],['w', 'w']],
        'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['3d', '3b', '2z'], ['2x', '2w', '2u']],'h':[['2s', '2q', '2o'], ['2m', '2k', '2i']], 'i':[['2g', '2e', '2c'], ['2a', '2d', '2g']], '1e':[['2j', '2m', '2p'], ['2s', '2v', '2y']], '1g':[['3b', '3a', '2x'], ['2u', '2r', '2o']], '1i':[['2l', '2i', '2f'], ['2c', '2e', '2i']]         
        }
#leaf_nodes_train=['3d', '3c', '3b', '3a', '2z','2y', '2x', '2w', '2v', '2u', '2t', '2s', '2r', '2q', '2p','2o', '2n', '2m', '2l', '2k','2j','2i','2h','2g','2f', '2e', '2d', '2c', '2b', '2a']

rules_pcfg4_id_mg = {
        'v':[['u'], ['s']], 
        'u':[ ['10#']], 's':[['10#'], ['10$'],['10$'], ['10#'], ['10*']],
        '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']],'10*':[['m', 'm'],['w', 'w']],
        'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2m', '2q', '2u'], ['2y', '3c', '2z']],'h':[['2v', '2r', '2n'], ['2j', '2f', '2b']], 'i':[['2f', '2k', '2p'], ['2u', '2z', '3c']], '1e':[['2x', '2s', '2n'], ['2i', '2d', '2g']], '1g':[['2m', '2s', '2y'], ['3c', '2w', '2q']], '1i':[['2k', '2e', '2c'], ['2h', '2o', '2v']]         
        }

leaf_nodes_id_mg=['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
grammar_NT_T_id_mg = ['v', 'w', 'x', '10$', '10#','10*', 'u', 's', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d', '1i', '1e', '1g']
sample_prob_id_mg = {
        'v':[0.5, 0.5], 
        'u':[1], 's':[0.2, 0.2, 0.2, 0.2, 0.2], 
        '10$':[0.5, 0.5], '10#':[0.5, 0.5], '10*':[0.5, 0.5],
        'n':[0.5, 0.5],  'm':[0.5, 0.5], 'w':[0.5, 0.5], 'x':[0.5, 0.5], 
        'l':[0.5, 0.5], 'k':[0.5, 0.5], 'j':[0.5, 0.5],'1f':[0.5, 0.5],'1h':[0.5, 0.5],
        'g':[0.5, 0.5], 'h':[0.5, 0.5], 'i':[0.5, 0.5] , '1e':[0.5, 0.5] , '1g':[0.5, 0.5] , '1i':[0.5, 0.5] 
        }









rules_pcfg1_ood_mg = {
        'v':[['s']], 
        's':[['10*']],
        '10*':[['m', 'x'],['w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l']], 
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2a', '2b', '2c'], ['2d', '2e', '2f']],'h':[['2h', '2i', '2j'], ['2k', '2l', '2m']], 'i':[['2n', '2o', '2p'], ['2q', '2r', '2s']], '1e':[['2t', '2u', '2v'], ['2w', '2x', '2y']], '1g':[['2z', '3a', '3b'], ['3c', '3d', '3c']], '1i':[['3b', '3a', '2z'], ['2y', '2x', '2w']]  }


rules_pcfg2_ood_mg = {
        'v':[['s']], 
        's':[['10*']],
        '10*':[['m', 'x'],['w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l']],
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2v', '2u', '2t'], ['2s', '2r', '2q']],'h':[['2p', '2o', '2n'], ['2m', '2l', '2k']], 'i':[['2j', '2i', '2h'], ['2g', '2f', '2e']], '1e':[['2d', '2c', '2b'], ['2a', '2c', '2e']], '1g':[['2g', '2i', '2k'], ['2m', '2o', '2q']], '1i':[['2s', '2u', '2w'], ['2y', '3a', '3c']] 
        }

#sampled length 236k

rules_pcfg3_ood_mg = {
        'v':[['s']], 
        's':[['10*']],
        '10*':[['m', 'x'],['w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l']],
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['3d', '3b', '2z'], ['2x', '2w', '2u']],'h':[['2s', '2q', '2o'], ['2m', '2k', '2i']], 'i':[['2g', '2e', '2c'], ['2a', '2d', '2g']], '1e':[['2j', '2m', '2p'], ['2s', '2v', '2y']], '1g':[['3b', '3a', '2x'], ['2u', '2r', '2o']], '1i':[['2l', '2i', '2f'], ['2c', '2e', '2i']]         
        }
#leaf_nodes_train=['3d', '3c', '3b', '3a', '2z','2y', '2x', '2w', '2v', '2u', '2t', '2s', '2r', '2q', '2p','2o', '2n', '2m', '2l', '2k','2j','2i','2h','2g','2f', '2e', '2d', '2c', '2b', '2a']

rules_pcfg4_ood_mg = {
        'v':[['s']], 
        's':[['10*']],
        '10*':[['m', 'x'],['w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l']],
        'l':[['1i', 'g'], ['i', '1i']], 'k':[['1e', 'g'], ['g', 'h']], 'j':[['i', '1e'], ['1g', 'h']], '1f':[['1i', 'h'], ['1i', '1e']], '1h':[['h', '1i'], ['1g', '1e']],
        'g':[['2m', '2q', '2u'], ['2y', '3c', '2z']],'h':[['2v', '2r', '2n'], ['2j', '2f', '2b']], 'i':[['2f', '2k', '2p'], ['2u', '2z', '3c']], '1e':[['2x', '2s', '2n'], ['2i', '2d', '2g']], '1g':[['2m', '2s', '2y'], ['3c', '2w', '2q']], '1i':[['2k', '2e', '2c'], ['2h', '2o', '2v']]         
        }

leaf_nodes_ood_mg=['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
grammar_NT_T_ood_mg = ['v', 'w', 'x', '10$', '10#', '10*', 'u', 's', 'o', 'm', 'l', 'k', 'j', 'i', 'h', 'g', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d', '1i', '1e', '1g']
sample_prob_ood_mg = {
        'v':[1], 
        's':[1], 
        '10*':[0.5, 0.5],
        'o':[0.5, 0.5], 'm':[0.5, 0.5], 'w':[0.5, 0.5], 'x':[0.5], 
        'l':[0.5, 0.5], 'k':[0.5, 0.5], 'j':[0.5, 0.5],'1f':[0.5, 0.5],'1h':[0.5, 0.5],
        'g':[0.5, 0.5], 'h':[0.5, 0.5], 'i':[0.5, 0.5] , '1e':[0.5, 0.5] , '1g':[0.5, 0.5] , '1i':[0.5, 0.5] 
        }





rules_pcfg1 = {
        'v':[['u', 't'], ['t', 's']], 
        'u':[['r', 'p'], ['p', '10$', 'q'], ['10#', 'r','q']], 't':[['q', 'p', 'r'], ['10*','p', 'q'], ['10$','r']], 's':[['p', '10#'], ['r', '10$', '10*'],['10$', '10*', '10#']],
        'r':[['o', 'n', 'm'], ['w', 'x', 'o']], 'q':[['w', 'o'], ['m', 'o', 'x']], 'p':[['m', 'n'], ['o', 'o', 'w']], '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']], '10*':[['m', 'm', 'x'],['w', 'w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2a', '2b', '2c'], ['2d', '2e', '2f']],'h':[['2h', '2i', '2j'], ['2k', '2l', '2m']], 'i':[['2n', '2o', '2p'], ['2q', '2r', '2s']], '1e':[['2t', '2u', '2v'], ['2w', '2x', '2y']], '1g':[['2z', '3a', '3b'], ['3c', '3d', '3c']], '1i':[['3b', '3a', '2z'], ['2y', '2x', '2w']] 
        }


rules_pcfg2 = {
        'v':[['u', 't'], ['t', 's']], 
        'u':[['r', 'p'], ['p', '10$', 'q'], ['10#', 'r','q']], 't':[['q', 'p', 'r'], ['10*','p', 'q'], ['10$','r']], 's':[['p', '10#'], ['r', '10$', '10*'],['10$', '10*', '10#']],
        'r':[['o', 'n', 'm'], ['w', 'x', 'o']], 'q':[['w', 'o'], ['m', 'o', 'x']], 'p':[['m', 'n'], ['o', 'o', 'w']], '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']], '10*':[['m', 'm', 'x'],['w', 'w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2v', '2u', '2t'], ['2s', '2r', '2q']],'h':[['2p', '2o', '2n'], ['2m', '2l', '2k']], 'i':[['2j', '2i', '2h'], ['2g', '2f', '2e']], '1e':[['2d', '2c', '2b'], ['2a', '2c', '2e']], '1g':[['2g', '2i', '2k'], ['2m', '2o', '2q']], '1i':[['2s', '2u', '2w'], ['2y', '3a', '3c']] 
        }

#sampled length 236k

rules_pcfg3 = {
        'v':[['u', 't'], ['t', 's']], 
        'u':[['r', 'p'], ['p', '10$', 'q'], ['10#', 'r','q']], 't':[['q', 'p', 'r'], ['10*','p', 'q'], ['10$','r']], 's':[['p', '10#'], ['r', '10$', '10*'],['10$', '10*', '10#']],
        'r':[['o', 'n', 'm'], ['w', 'x', 'o']], 'q':[['w', 'o'], ['m', 'o', 'x']], 'p':[['m', 'n'], ['o', 'o', 'w']], '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']], '10*':[['m', 'm', 'x'],['w', 'w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['3d', '3b', '2z'], ['2x', '2w', '2u']],'h':[['2s', '2q', '2o'], ['2m', '2k', '2i']], 'i':[['2g', '2e', '2c'], ['2a', '2d', '2g']], '1e':[['2j', '2m', '2p'], ['2s', '2v', '2y']], '1g':[['3b', '3a', '2x'], ['2u', '2r', '2o']], '1i':[['2l', '2i', '2f'], ['2c', '2e', '2i']] 
        }
#leaf_nodes_train=['3d', '3c', '3b', '3a', '2z','2y', '2x', '2w', '2v', '2u', '2t', '2s', '2r', '2q', '2p','2o', '2n', '2m', '2l', '2k','2j','2i','2h','2g','2f', '2e', '2d', '2c', '2b', '2a']

rules_pcfg4 = {
        'v':[['u', 't'], ['t', 's']], 
        'u':[['r', 'p'], ['p', '10$', 'q'], ['10#', 'r','q']], 't':[['q', 'p', 'r'], ['10*','p', 'q'], ['10$','r']], 's':[['p', '10#'], ['r', '10$', '10*'],['10$', '10*', '10#']],
        'r':[['o', 'n', 'm'], ['w', 'x', 'o']], 'q':[['w', 'o'], ['m', 'o', 'x']], 'p':[['m', 'n'], ['o', 'o', 'w']], '10$':[['x', 'w', 'm'],['n', 'w', 'n']], '10#':[['n', 'x', 'x'],['n', 'n', 'x']], '10*':[['m', 'm', 'x'],['w', 'w', 'o']], 
        'o':[['l', 'k', 'j'], ['l', '1h', 'j']],  'n':[['k', '1h', '1f'], ['k', 'l', 'j']], 'm':[['l', 'k', '1f'], ['1f', '1h', 'l']], 'w':[['1f', '1h', '1h'], ['l', '1f', 'j']], 'x':[['j', 'j', 'l'], ['1f', 'l']], 
        'l':[['1i', 'i', 'g'], ['i', '1i', 'g']], 'k':[['1e', 'g', 'i'], ['1g', 'g', 'h']], 'j':[['i', '1e', '1i'], ['1g', 'h', '1e']], '1f':[['1i', 'h', '1g'], ['1i', '1e', 'h']], '1h':[['h', '1i', '1g'], ['1g', '1e', 'h']],
        'g':[['2m', '2q', '2u'], ['2y', '3c', '2z']],'h':[['2v', '2r', '2n'], ['2j', '2f', '2b']], 'i':[['2f', '2k', '2p'], ['2u', '2z', '3c']], '1e':[['2x', '2s', '2n'], ['2i', '2d', '2g']], '1g':[['2m', '2s', '2y'], ['3c', '2w', '2q']], '1i':[['2k', '2e', '2c'], ['2h', '2o', '2v']] 
        }

leaf_nodes=['2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d']
grammar_NT_T = ['v', 'w', 'x', '10$', '10#', '10*', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', '2a', '2b', '2c', '2d', '2e','2f', '2g', '2h', '2i', '2j', '2k', '2l', '2m', '2n', '2o','2p', '2q', '2r', '2s', '2t','2u','2v','2w','2x','2y', '2z', '3a', '3b', '3c', '3d', '1i', '1e', '1g']

sample_prob_pcfg = {
        'v':[0.5, 0.5], 
        'u':[0.33, 0.33, 0.33], 't':[0.33, 0.33, 0.33], 's':[0.33, 0.33, 0.33], 
        'r':[0.5, 0.5], 'q':[0.5, 0.5], 'p':[0.5, 0.5], '10$':[0.5, 0.5], '10#':[0.5, 0.5], '10*':[0.5, 0.5],
        'o':[0.5, 0.5], 'n':[0.5, 0.5],  'm':[0.5, 0.5], 'w':[0.5, 0.5], 'x':[0.5, 0.5], 
        'l':[0.5, 0.5], 'k':[0.5, 0.5], 'j':[0.5, 0.5],'1f':[0.5, 0.5],'1h':[0.5, 0.5], 
        'g':[0.5, 0.5], 'h':[0.5, 0.5], 'i':[0.5, 0.5] , '1e':[0.5, 0.5] , '1g':[0.5, 0.5] , '1i':[0.5, 0.5] 
        }




rules_pcfg = []
lst_pcfg_names = []
for i in range(args.num_pcfg):
    if args.sample_pcfg_number1==i+1:
        rules_pcfg.append(rules_pcfg1_unsafe)
        lst_pcfg_names.append(1)
    elif args.sample_pcfg_number2==i+1:
        rules_pcfg.append(rules_pcfg2_unsafe)
        lst_pcfg_names.append(2)
    elif args.sample_pcfg_number3==i+1:
        rules_pcfg.append(rules_pcfg3_unsafe)
        lst_pcfg_names.append(3)
    elif args.sample_pcfg_number4==i+1:
        rules_pcfg.append(rules_pcfg4_unsafe)
        lst_pcfg_names.append(4)


#### 0 = unsafe, 1 = safe, 2 = intermediate, 3 = all, 4 = duplicate, 5 = id_mg, 6 = ood_mg
train_dataset = DGP_sample(args,split='train',seed_lst=seed_lst_train, num_samples=args.num_samples_train,loader_unsafe=load_train_unsafe, loader_safe=load_train_safe, loader_duplicate=load_train_duplicate, loader_intermediate=load_train_intermediate, loader_id_mg=load_train_id_mg, loader_ood_mg = load_train_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names,safe_branch_prob=args.safe_branch_prob, unsafe_branch_prob=args.unsafe_branch_prob, intermediate_prob=args.intermediate_prob, prob_all=args.prob_all, duplicate_prob=args.duplicate_prob, id_mg_prob=args.id_mg_prob, ood_mg_prob=args.ood_mg_prob, is_safe_value=0)
val_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_val, num_samples=args.num_samples_val,rules_pass=train_dataset.capability_rules, loader_unsafe=load_val_unsafe, loader_safe=load_val_safe,  loader_duplicate=load_val_duplicate, loader_intermediate=load_val_intermediate, loader_id_mg=load_val_id_mg, loader_ood_mg = load_val_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1)

test_dataset_unsafe = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=0)
test_dataset_safe = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,  loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1)
test_dataset_intermediate = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules, loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=2)
test_dataset_all = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,  loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=2)
test_dataset_duplicate = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,  loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=4)
test_dataset_id_mg = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=5)
test_dataset_ood_mg = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=6)

test_dataset_id_jailbreak_direct = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=5, data_inst_fl_direct=True)
test_dataset_safe_jailbreak_direct = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1, data_inst_fl_direct=True)

test_dataset_id_jailbreak_comp = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=5, data_inst_fl_comp=True)
test_dataset_safe_jailbreak_comp = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1, data_inst_fl_comp=True)

if args.perform_co==True:
    test_dataset_safe_co = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1)
    test_dataset_id_co = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=5)

##### utilities: train-> unsafe and safe only are used for training. for filter p(safe)=1 and for mix-match p(safe)=0.2, p(unsafe)=0.8 
############### unsafe-> aversarial attack (both untargeted and targeted), normal evaluation to see if safety fine-tuning is actually working (this can different based on the protocol)
############### safe:-> adversarial attack (both untargeted and targeted), normal evlution to see if model still performs well on safe data.
############### intermediate:-> competitive objectives jailbreaking attacks, 
###############  all :-> original performance
############### duplicate:-> jailbreaking attacks mismacthed generalization
############### id_mg:-> unsafe data in-domain, normal evaluation
############### ood_mg:-> unsafe data out of domain, normal evaluation

val_dataset.allowed_max_window_length = train_dataset.allowed_max_window_length
test_dataset_unsafe.allowed_max_window_length = train_dataset.allowed_max_window_length
test_dataset_safe.allowed_max_window_length = train_dataset.allowed_max_window_length
test_dataset_intermediate.allowed_max_window_length = train_dataset.allowed_max_window_length
test_dataset_all.allowed_max_window_length = train_dataset.allowed_max_window_length
test_dataset_duplicate.allowed_max_window_length = train_dataset.allowed_max_window_length
test_dataset_id_mg.allowed_max_window_length = train_dataset.allowed_max_window_length
test_dataset_ood_mg.allowed_max_window_length = train_dataset.allowed_max_window_length



model_config = GPT.get_default_config()
model_config.embedding_type = args.embedding_type
model_config.max_relative_position = args.max_relative_position
model_config.model_type = args.model_type
model_config.scale_internal = args.scale_internal
model_config.n_layer = args.n_layer
model_config.n_head = args.n_head
model_config.pad_token = args.pad_token
model_config.n_embd = args.n_embd
model_config.vocab_size = train_dataset.vocab_size
model_config.block_size = args.block_size
model_config.embd_pdrop = args.embd_pdrop
model_config.resid_pdrop = args.resid_pdrop
model_config.attn_pdrop = args.attn_pdrop

model_config.vocab_size = train_dataset.get_vocab_size()
model_config.block_size = train_dataset.allowed_max_window_length

if args.is_dataparallel==1:
    model = torch.nn.DataParallel(GPT(train_dataset.tokenizer, model_config))
    model.load_state_dict(torch.load(args.model_load_path))


else:
    model = GPT(train_dataset.tokenizer, model_config)
    model.load_state_dict(torch.load(args.model_load_path))


model_config2 = GPT.get_default_config()
model_config2.embedding_type = args.embedding_type
model_config2.max_relative_position = args.max_relative_position
model_config2.model_type = args.model_type
model_config2.scale_internal = args.scale_internal
model_config2.n_layer = args.n_layer
model_config2.n_head = args.n_head
model_config2.pad_token = args.pad_token
model_config2.n_embd = args.n_embd
model_config2.vocab_size = train_dataset.vocab_size
model_config2.block_size = args.block_size
model_config2.embd_pdrop = args.embd_pdrop
model_config2.resid_pdrop = args.resid_pdrop
model_config2.attn_pdrop = args.attn_pdrop

model_config2.vocab_size = train_dataset.get_vocab_size()
model_config2.block_size = train_dataset.allowed_max_window_length

if args.is_dataparallel==1:
    model2 = torch.nn.DataParallel(GPT(train_dataset.tokenizer, model_config2)).cuda()
    model2.load_state_dict(torch.load(args.model_load_path2))
else:
    model2 = GPT(train_dataset.tokenizer, model_config2).cuda()
    model2.load_state_dict(torch.load(args.model_load_path2))
model2.eval()

train_config = Trainer.get_default_config()
train_config.device = args.device
train_config.is_dataparallel = args.is_dataparallel
train_config.save_iter = args.save_iter
train_config.val_iter = args.val_iter
train_config.val_evaluate_iter = args.val_evaluate_iter
train_config.train_evaluate_iter = args.train_evaluate_iter
train_config.test_evaluate_iter = args.test_evaluate_iter
train_config.num_workers = args.num_workers
train_config.max_iters = args.max_iters
train_config.pad_token = args.pad_token
train_config.tokenizer = train_dataset.tokenizer
train_config.max_window_possible = args.max_window_possible
train_config.learning_rate = args.learning_rate
train_config.min_lr = args.min_lr
train_config.batch_size = args.batch_size
train_config.test_batch_size = args.test_batch_size
train_config.decay_lr = args.decay_lr
train_config.warmup_iters = args.warmup_iters
train_config.lr_decay_iters = args.lr_decay_iters
train_config.weight_decay = args.weight_decay
train_config.grad_norm_clip = args.grad_norm_clip
train_config.betas = (args.beta1, args.beta2)
train_config.save_path = args.save_path
train_config.model_load_path = args.model_load_path
train_config.optimizer_load_path = args.optimizer_load_path
train_config.start_iter_num = args.start_iter_num
train_config.eps_soft_prompt = args.eps_soft_prompt
train_config.eps_soft_paraphrase = args.eps_soft_paraphrase
train_config.attack_norm = args.attack_norm
train_config.vocab_size = train_dataset.vocab_size

train_config.task_tokens = args.num_cap
train_config.attack_adv = args.attack_adv
train_config.attack_adv_targeted = args.attack_adv_targeted
train_config.attack_jailbreak_mg_text = args.attack_jailbreak_mg_text
train_config.attack_jailbreak_mg_tokens = args.attack_jailbreak_mg_tokens
train_config.attack_jailbreak_co = args.attack_jailbreak_co
train_config.threat_count_adv = args.threat_count_adv
train_config.threat_pos_adv = args.threat_pos_adv
train_config.adv_attack_norm = args.adv_attack_norm
train_config.adv_attack_iters = args.adv_attack_iters
train_config.jail_mg_para_attack_iters = args.jail_mg_para_attack_iters
train_config.jail_mg_para_attack_norm = args.jail_mg_para_attack_norm
train_config.jail_mg_para_frac = args.jail_mg_para_frac
train_config.jail_mg_para_attack_type = args.jail_mg_para_attack_type
train_config.n_embd = args.n_emb_value
train_config.num_cap = args.num_cap
train_config.train_type = args.train_type
train_config.prob_safe = args.prob_safe 
train_config.is_dpo = args.is_dpo
train_config.dpo_weight_safe = args.dpo_weight_safe
train_config.dpo_weight_unsafe = args.dpo_weight_unsafe
train_config.prob_unsafe = args.prob_unsafe
train_config.dpo_model = model2
train_config.perform_co = args.perform_co
train_config.univ_adv = args.univ_adv

model.eval()

num_layers=6


def evaluate(model, loader, max_iterations=0,is_safety=0,safe=0):
        model.eval()
        iter_counter = 0
        acc = 0
        loss_total = 0
        model.eval()
        num_counter = 0
        counter=0
        txt_new_lst = []
        start_idx_lst = []
        attention_pattern_act_lst2 = []
        attention_pattern_act_lst = []
        attention_pattern_residual_lst = []
        attention_pattern_copy_lst = []
        end_idx_lst = []
        acc_comb1 = 0
        acc_idx1 = 0
        acc_idx12 = 0
        acc_comb12 = 0
        
        for batch in loader:
            flag = 0
            x_safe_cap, x_unsafe_cap, x_unsafe_cap_target, y_safe_cap, y_unsafe_cap, y_unsafe_cap_target, mask, start_idx, end_idx, idx, idx1, idx2, idx3, idx_clm, is_safe, sample_idx = batch
            start_idx_lst.append(start_idx[0].detach().int())

            end_idx_lst.append(end_idx[0][0].detach().int())
            if is_safety==1:
                x = x_safe_cap.cuda()
                y = y_safe_cap.cuda()
                y_tar = y_safe_cap.cuda()
            else:
                x = x_unsafe_cap_target.cuda()
                y = y_unsafe_cap_target.cuda()
                y_tar = x_unsafe_cap.cuda()
            mask = mask.cuda()
            logits, att_lst,c, att_lst_act, att_lst_residual, att_lst_copy, _ = model(x,mask=mask)

            for i in range(y.shape[0]):
                acc_idx1_temp = (logits[i][start_idx[i]:start_idx[i]+1].argmax(dim=-1)==y[i][start_idx[i]:start_idx[i]+1])
                acc_idx1+=torch.sum(acc_idx1_temp/acc_idx1_temp.shape[0])
                if torch.sum(acc_idx1_temp)==1 or safe==1:
                    flag=0
                else:
                    flag = 1

                
            counter+=1

            if counter==1001:
                break
               
            for i in range(y.shape[0]):
                acc_idx1_temp = (logits[i][start_idx[i]:end_idx[i][0]].argmax(dim=-1)==y[i][start_idx[i]:end_idx[i][0]])
                acc_idx1+=torch.sum(acc_idx1_temp/acc_idx1_temp.shape[0])

                acc_idx1_temp2 = (logits[i][start_idx[i]:end_idx[i][0]].argmax(dim=-1)==y_tar[i][start_idx[i]:end_idx[i][0]])
                acc_idx12+=torch.sum(acc_idx1_temp2/acc_idx1_temp2.shape[0])


                if torch.sum(acc_idx1_temp)==(end_idx[i][0]-start_idx[i]):
                    acc_comb1+=1

                if torch.sum(acc_idx1_temp2)==(end_idx[i][0]-start_idx[i]):
                    acc_comb12+=1






            
            #for i in range(att_lst):
            attention_pattern = []
            txt_new = []
            #attention_pattern.append(att_lst[i].detach().cpu().numpy().tolist())
            for layer_num in range(num_layers):
                #print("Layer Number", layer_num)
                att_lst2 = []
                for k in range(1):
                    att_lst2.append(att_lst[layer_num].detach().cpu().numpy()[0][start_idx[0], :])
                attention_pattern.append(att_lst2)


            #for i in range(att_lst):
            attention_pattern_act = []
            txt_new = []
            for layer_num in range(num_layers):
                att_lst2 = []
                for k in range(1):
                    att_lst2.append(att_lst_act[layer_num].detach().cpu().numpy()[0][start_idx[0], :])
                attention_pattern_act.append(att_lst2)


            #for i in range(att_lst):
            attention_pattern_residual = []
            txt_new = []
            #attention_pattern.append(att_lst[i].detach().cpu().numpy().tolist())
            for layer_num in range(num_layers):
                #print("Layer Number", layer_num)
                att_lst2 = []
                for k in range(1):
                    att_lst2.append(att_lst_residual[layer_num].detach().cpu().numpy()[0][start_idx[0], :])
                attention_pattern_residual.append(att_lst2)


            #for i in range(att_lst):
            attention_pattern_copy = []
            txt_new = []
            #attention_pattern.append(att_lst[i].detach().cpu().numpy().tolist())
            for layer_num in range(num_layers):
                #print("Layer Number", layer_num)
                att_lst2 = []
                for k in range(1):
                    att_lst2.append(att_lst_copy[layer_num].detach().cpu().numpy()[0][start_idx[0], :])
                attention_pattern_copy.append(att_lst2)


            #print(x.shape)
            #a+=1
            x_mod = x.detach().cpu().numpy()[0,:80].tolist()
            for k in range(80):
                txt_new.append(reverse_tokenizer[x_mod[k]])

            attention_pattern_act_lst2.append(attention_pattern)
            attention_pattern_act_lst.append(attention_pattern_act)
            attention_pattern_residual_lst.append(attention_pattern_residual)
            attention_pattern_copy_lst.append(attention_pattern_copy)
            txt_new_lst.append(txt_new)
            

        acc_noand = []
        acc_and = []

        acc_noand = acc_idx1.detach().cpu().float()/1000
        acc_and = acc_comb1/1000

        acc_unsafe_noand = acc_idx12.detach().cpu().float()/1000
        acc_unsafe_and = acc_comb12/1000


        return attention_pattern_act_lst2, attention_pattern_act_lst, attention_pattern_residual_lst, attention_pattern_copy_lst, txt_new_lst, start_idx_lst, end_idx_lst, acc_noand, acc_and, acc_unsafe_noand, acc_unsafe_and


def get_svd(arr):
    mu =  np.mean(arr, axis=0)
    arr = arr - mu
    U, S, V = np.linalg.svd(arr, full_matrices=True)
    return U,  V, S


if args.data_test=='std_unsafe':
    test_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=5)
elif args.data_test=='std_safe':
    test_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,  loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1)
elif args.data_test=='mg_tokens':
    test_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,  loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=4)
elif args.data_test=='mg_txt':
    test_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=6)
elif args.data_test=='if_text_safe':
    test_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1, data_inst_fl_direct=True)
elif args.data_test=='if_text_unsafe':
    test_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=5, data_inst_fl_direct=True)
elif args.data_test=='if_txt':
    test_dataset= DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules, loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=2)
elif args.data_test=='if_comp_safe':
    test_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1, data_inst_fl_comp=True)
elif args.data_test=='if_comp_unsafe':
    test_dataset = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,   loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=5, data_inst_fl_comp=True)



reverse_tokenizer = test_dataset.reverse_tokenizer
test_dataset_sb = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,  loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=1)
test_dataset_ub = DGP_sample(args,split='test',seed_lst=seed_lst_test, num_samples=args.num_samples_test,rules_pass=train_dataset.capability_rules,  loader_unsafe=load_test_unsafe, loader_safe=load_test_safe,  loader_duplicate=load_test_duplicate, loader_intermediate=load_test_intermediate, loader_id_mg=load_test_id_mg, loader_ood_mg = load_test_ood_mg, leaf_nodes=leaf_nodes, grammar_NT_T=grammar_NT_T, rules=rules_pcfg, pcfg_num=lst_pcfg_names, is_safe_value=5)


test_loader = DataLoader(test_dataset,shuffle=False,pin_memory=True,batch_size=args.batch_size,num_workers=args.num_workers)
test_loader_sb = DataLoader(test_dataset_sb,shuffle=False,pin_memory=True,batch_size=args.batch_size,num_workers=args.num_workers)
test_loader_ub = DataLoader(test_dataset_ub,shuffle=False,pin_memory=True,batch_size=args.batch_size,num_workers=args.num_workers)



counter=0
mpl.rcParams['xtick.labelsize'] = 6
mpl.rcParams['ytick.labelsize'] = 6

mpl.rcParams['xtick.labelsize'] = 6
mpl.rcParams['ytick.labelsize'] = 6
lst_sim_right = []
lst_sim_left = []
lst_theta_safe = []
lst_theta_unsafe = []

lst_theta2_safe = []
lst_theta2_unsafe = []

plane_lst_theta_safe = []
plane_lst_theta_unsafe = []

plane_lst_theta2_safe = []
plane_lst_theta2_unsafe = []

fig, axs = plt.subplots(2, 3, figsize=(6, 4))

if args.data_test=='mg_tokens':
    attention_pattern_lst_unsafe, attention_pattern_act_lst_unsafe, attention_pattern_residual_lst_unsafe, attention_pattern_copy_lst_unsafe,  input_seq_lst_unsafe,_,_,_,_,_,_  = evaluate(model, test_loader, max_iterations=args.test_evaluate_iter, is_safety=1)
    attention_pattern_lst_safe, attention_pattern_act_lst_safe, attention_pattern_residual_lst_safe, attention_pattern_copy_lst_safe,  input_seq_lst_safe,_,_,_,_,_,_  = evaluate(model, test_loader_sb, max_iterations=args.test_evaluate_iter, is_safety=1,safe=1)
else:
    attention_pattern_lst_unsafe, attention_pattern_act_lst_unsafe, attention_pattern_residual_lst_unsafe, attention_pattern_copy_lst_unsafe,   input_seq_lst_unsafe,_,_,_,_,_,_  = evaluate(model, test_loader, max_iterations=args.test_evaluate_iter, is_safety=0)
    attention_pattern_lst_safe, attention_pattern_act_lst_safe, attention_pattern_residual_lst_safe, attention_pattern_copy_lst_safe,  input_seq_lst_safe,_,_,_,_,_,_  = evaluate(model, test_loader, max_iterations=args.test_evaluate_iter, is_safety=1,safe=1)


for layer_num in range(num_layers):

    val_arr = model.module.transformer.h[layer_num].c_fc.weight.detach().cpu().numpy()
    val_arr_pretrain = model2.module.transformer.h[layer_num].c_fc.weight.detach().cpu().numpy()

    val_arr_diff = val_arr_pretrain
    left_sv, right_sv, sing_values = get_svd(val_arr_diff)
    lst_max = []
    lst_cos = []

    lst_index = []
    for i in range(len(attention_pattern_lst_unsafe)):
        act_unsafe =  np.reshape(np.array(attention_pattern_lst_unsafe[i][layer_num][0]),-1)
        # print("act_unsafe", act_unsafe.shape)
        max_value = 0
        index_max_lst = []
        for j in range(len(right_sv)):
            # print("right_sv", right_sv[0].shape)
            cos_sim = sing_values[j]*np.sum(np.dot(act_unsafe, right_sv[j]))/(np.linalg.norm(act_unsafe)*np.linalg.norm(right_sv[j]))
            index_max_lst.append(cos_sim)
        # cos_sim = np.sum(np.dot(val_arr[index_max], val_arr_pretrain[index_max]))/(np.linalg.norm(val_arr[index_max])*np.linalg.norm(val_arr_pretrain[index_max]))
        # print("max_value", max_value)
        lst_index.append(index_max_lst)
        # lst_cos.append(cos_sim)

    lst_index_safe = []
    for i in range(len(attention_pattern_lst_safe)):
        act_unsafe =  np.reshape(np.array(attention_pattern_lst_safe[i][layer_num][0]),-1)
        # print("act_unsafe", act_unsafe.shape)
        max_value = 0
        index_max_lst = []
        for j in range(len(right_sv)):
            # print("right_sv", right_sv[0].shape)
            cos_sim = sing_values[j]*np.sum(np.dot(act_unsafe, right_sv[j]))/(np.linalg.norm(act_unsafe)*np.linalg.norm(right_sv[j]))
            index_max_lst.append(cos_sim)
        # cos_sim = np.sum(np.dot(val_arr[index_max], val_arr_pretrain[index_max]))/(np.linalg.norm(val_arr[index_max])*np.linalg.norm(val_arr_pretrain[index_max]))
        # print("max_value", max_value)
        lst_index_safe.append(index_max_lst)
        # lst_cos.append(cos_sim

    if layer_num>=3:
        input_val = layer_num-3
        id=1
    else:
        input_val = layer_num
        id=0

    np.save("understand_transformation_learned_all_indices_proj_avg_w/"+ args.plot_path+"_unsafe_{}".format(layer_num)+"_"+ args.data_test+ ".npy", np.array(lst_index))
    np.save("understand_transformation_learned_all_indices_proj_avg_w/"+ args.plot_path+"_safe_{}".format(layer_num)+"_"+ args.data_test+ ".npy", np.array(lst_index_safe))
    

#fig.legend([l1_safe, l2_safe, l3_safe],["cos-sim", "sing-val", "sing-val-pre"],loc='upper center',fontsize=4)
plt.savefig("./understand_transformation_learned_all_indices_proj_avg_w/" + args.plot_path + '_hist_' + args.data_test + "_AM.pdf")
plt.close('all')