import sys
import subprocess
import os

# --- SISTEMA DE AUTO-INSTALAÇÃO DAS BIBLIOTECAS ---
try:
    import customtkinter as ctk
except ImportError:
    print("Instalando CustomTkinter... Por favor, aguarde alguns segundos.")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import json

# Configuração visual premium (Dark Mode)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GerenciadorEstoqueLotesAlmeida(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela Principal
        self.title("Almeida Stock Master v3.0 — Controle Ativo de Validades")
        self.geometry("1200x720")
        self.configure(fg_color="#0a0a0c")

        # Arquivos de persistência (Backend)
        self.arquivo_banco = "banco_estoque.json"
        self.arquivo_supervisor_saida = "relatorio_para_supervisor.json"
        self.arquivo_supervisor_entrada = "comandos_supervisor.json"

        # Carrega os dados locais
        self.carregar_dados_locais()
        self.faturamento_dia = 0.0

        # Interface gráfica
        self.criar_cabecalho()
        
        # Abas
        self.tabview = ctk.CTkTabview(self, fg_color="#111115", border_width=1, border_color="#1e1e24", corner_radius=14)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.tab_movimentacao = self.tabview.add("📦 Movimentação de Lotes")
        self.tab_cadastro = self.tabview.add("➕ Cadastrar Novo Produto")
        self.tab_supervisor = self.tabview.add("📡 Comandos do Supervisor")

        self.configurar_aba_movimentacao()
        self.configurar_aba_cadastro()
        self.configurar_aba_supervisor()

    def criar_cabecalho(self):
        frame_topo = ctk.CTkFrame(self, height=60, fg_color="#111115", corner_radius=0)
        frame_topo.pack(fill=tk.X, side=tk.TOP)
        frame_topo.pack_propagate(False)

        lbl_logo = ctk.CTkLabel(frame_topo, text="📦 ALMEIDA STOCK MASTER v3.0", font=("Segoe UI", 16, "bold"), text_color="white")
        lbl_logo.pack(side=tk.LEFT, padx=20, pady=15)

        self.lbl_status_conexao = ctk.CTkLabel(frame_topo, text="Link com a Gerência: Ativo 🟢", font=("Segoe UI", 12, "bold"), text_color="#2ecc71")
        self.lbl_status_conexao.pack(side=tk.RIGHT, padx=20, pady=15)

    def configurar_aba_movimentacao(self):
        frame_form = ctk.CTkFrame(self.tab_movimentacao, width=360, fg_color="transparent")
        frame_form.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        frame_form.pack_propagate(False)

        ctk.CTkLabel(frame_form, text="Lançar Movimentação", font=("Segoe UI", 14, "bold"), text_color="white").pack(pady=10, anchor="w")

        ctk.CTkLabel(frame_form, text="Código do Produto (ID):", text_color="#6e6e77").pack(anchor="w")
        self.entry_mov_id = ctk.CTkEntry(frame_form, placeholder_text="Ex: 001", fg_color="#18181c", border_color="#2b2b36")
        self.entry_mov_id.pack(fill=tk.X, pady=(5, 10))

        ctk.CTkLabel(frame_form, text="Número do Lote:", text_color="#6e6e77").pack(anchor="w")
        self.entry_mov_lote = ctk.CTkEntry(frame_form, placeholder_text="Ex: LOTE A", fg_color="#18181c", border_color="#2b2b36")
        self.entry_mov_lote.pack(fill=tk.X, pady=(5, 10))

        ctk.CTkLabel(frame_form, text="Quantidade (Caixas):", text_color="#6e6e77").pack(anchor="w")
        self.entry_mov_qtd = ctk.CTkEntry(frame_form, placeholder_text="Ex: 150", fg_color="#18181c", border_color="#2b2b36")
        self.entry_mov_qtd.pack(fill=tk.X, pady=(5, 10))

        ctk.CTkLabel(frame_form, text="Data de Validade (Apenas p/ Entrada):", text_color="#6e6e77").pack(anchor="w")
        self.entry_mov_validade = ctk.CTkEntry(frame_form, placeholder_text="DD/MM/AAAA", fg_color="#18181c", border_color="#2b2b36")
        self.entry_mov_validade.pack(fill=tk.X, pady=(5, 15))

        ctk.CTkLabel(frame_form, text="Operação:", text_color="#6e6e77").pack(anchor="w")
        self.var_operacao = tk.StringVar(value="Venda")
        ctk.CTkRadioButton(frame_form, text="Saída (Despachar / Venda)", variable=self.var_operacao, value="Venda", fg_color="#e74c3c").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(frame_form, text="Entrada (Abastecer Estoque)", variable=self.var_operacao, value="Entrada", fg_color="#2ecc71").pack(anchor="w", pady=5)

        btn_aplicar = ctk.CTkButton(frame_form, text="Confirmar Operação", font=("Segoe UI", 12, "bold"), height=38, fg_color="#1f77b4", command=self.processar_movimentacao)
        btn_aplicar.pack(fill=tk.X, pady=20)

        frame_visu = ctk.CTkFrame(self.tab_movimentacao, fg_color="transparent")
        frame_visu.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.lbl_faturamento = ctk.CTkLabel(frame_visu, text="FATURAMENTO SESSÃO: R$ 0.00", font=("Segoe UI", 13, "bold"), text_color="#2ecc71", anchor="w")
        self.lbl_faturamento.pack(pady=(0, 10))

        self.scroll_estoque = ctk.CTkScrollableFrame(frame_visu, fg_color="#0a0a0c", border_width=1, border_color="#1e1e24")
        self.scroll_estoque.pack(fill=tk.BOTH, expand=True)
        
        self.atualizar_tabela_lotes()

    def configurar_aba_cadastro(self):
        frame_cad = ctk.CTkFrame(self.tab_cadastro, width=500, fg_color="#18181c", border_width=1, border_color="#2b2b36", corner_radius=12)
        frame_cad.pack(pady=40, padx=20)

        ctk.CTkLabel(frame_cad, text="📝 Formulário de Cadastro", font=("Segoe UI", 16, "bold"), text_color="white").pack(pady=20)

        ctk.CTkLabel(frame_cad, text="Código Único (ID):", text_color="#6e6e77").pack(anchor="w", padx=40)
        self.entry_cad_id = ctk.CTkEntry(frame_cad, placeholder_text="Ex: 003", width=420, fg_color="#0a0a0c")
        self.entry_cad_id.pack(pady=(5, 15))

        ctk.CTkLabel(frame_cad, text="Nome do Produto:", text_color="#6e6e77").pack(anchor="w", padx=40)
        self.entry_cad_nome = ctk.CTkEntry(frame_cad, placeholder_text="Ex: Fardo de Arroz 1kg", width=420, fg_color="#0a0a0c")
        self.entry_cad_nome.pack(pady=(5, 15))

        ctk.CTkLabel(frame_cad, text="Preço da Caixa (R$):", text_color="#6e6e77").pack(anchor="w", padx=40)
        self.entry_cad_preco = ctk.CTkEntry(frame_cad, placeholder_text="Ex: 58.90", width=420, fg_color="#0a0a0c")
        self.entry_cad_preco.pack(pady=(5, 25))

        btn_cadastrar = ctk.CTkButton(frame_cad, text="Salvar Produto no Sistema", font=("Segoe UI", 13, "bold"), fg_color="#2ecc71", hover_color="#27ae60", height=40, command=self.cadastrar_novo_produto)
        btn_cadastrar.pack(pady=(0, 30), padx=40, fill=tk.X)

    def configurar_aba_supervisor(self):
        frame_sup = ctk.CTkFrame(self.tab_supervisor, fg_color="transparent")
        frame_sup.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        frame_botoes = ctk.CTkFrame(frame_sup, fg_color="#18181c", height=70, corner_radius=10)
        frame_botoes.pack(fill=tk.X, pady=(0, 15))
        frame_botoes.pack_propagate(False)

        ctk.CTkLabel(frame_botoes, text="Painel de Comunicação Direta", font=("Segoe UI", 13, "bold"), text_color="white").pack(side=tk.LEFT, padx=20)
        
        btn_checar_ordens = ctk.CTkButton(frame_botoes, text="🔄 CHECAR ORDENS DO SUPERVISOR", font=("Segoe UI", 12, "bold"), fg_color="#9b59b6", hover_color="#8e44ad", command=self.ler_comandos_supervisor)
        btn_checar_ordens.pack(side=tk.RIGHT, padx=10, pady=15)

        btn_enviar = ctk.CTkButton(frame_botoes, text="🚀 ENVIAR FECHAMENTO DE ESTOQUE", font=("Segoe UI", 12, "bold"), fg_color="#e67e22", hover_color="#d35400", command=self.exportar_para_supervisor)
        btn_enviar.pack(side=tk.RIGHT, padx=10, pady=15)

        ctk.CTkLabel(frame_sup, text="📋 Diretrizes e Relatórios Enviados pelo Supervisor ao Operador:", font=("Segoe UI", 12, "bold"), text_color="#3498db").pack(anchor="w", pady=(10, 5))
        
        self.txt_comandos_recebidos = ctk.CTkTextbox(frame_sup, fg_color="#0a0a0c", border_width=1, border_color="#1e1e24", font=("Segoe UI", 12), text_color="#f1c40f")
        self.txt_comandos_recebidos.pack(fill=tk.BOTH, expand=True)
        
        self.ler_comandos_supervisor()

    def carregar_dados_locais(self):
        if os.path.exists(self.arquivo_banco):
            try:
                with open(self.arquivo_banco, "r", encoding="utf-8") as f:
                    self.banco_produtos = json.load(f)
                return
            except:
                pass
        
        self.banco_produtos = {
            "001": {
                "nome": "Coca-Cola Lata",
                "preco": 5.00,
                "lotes": {
                    "LOTE 1": {"qtd": 400, "validade": "18/12/2026"},
                    "LOTE 2": {"qtd": 150, "validade": "28/05/2026"}
                }
            },
            "002": {
                "nome": "Água Mineral 500ml",
                "preco": 3.00,
                "lotes": {
                    "LOTE 1": {"qtd": 1200, "validade": "15/01/2027"}
                }
            }
        }
        self.salvar_dados_locais()

    def salvar_dados_locais(self):
        with open(self.arquivo_banco, "w", encoding="utf-8") as f:
            json.dump(self.banco_produtos, f, indent=4, ensure_ascii=False)

    def ler_comandos_supervisor(self):
        self.txt_comandos_recebidos.delete("1.0", tk.END)
        
        if not os.path.exists(self.arquivo_supervisor_entrada):
            exemplo_comando = {
                "ultima_atualizacao_supervisor": "18/05/2026 19:30",
                "mensagem_urgente": "Atenção Operador: Favor priorizar a saída do LOTE 2 de Coca-Cola pois está próximo do vencimento na triagem físico-sistema. Favor realizar conferência visual no palete 4.",
                "metas_do_turno": ["Bater estoque de refrigerantes", "Organizar setor de caixas de água"]
            }
            with open(self.arquivo_supervisor_entrada, "w", encoding="utf-8") as f:
                json.dump(exemplo_comando, f, indent=4, ensure_ascii=False)

        try:
            with open(self.arquivo_supervisor_entrada, "r", encoding="utf-8") as f:
                dados = json.load(f)
                
            texto = f"📡 RELATÓRIO DO SUPERVISOR RECEBIDO EM: {dados.get('ultima_atualizacao_supervisor', 'N/A')}\n"
            texto += f"{'='*70}\n\n"
            texto += f"📢 MENSAGEM DO SUPERVISOR:\n{dados.get('mensagem_urgente', 'Sem avisos novos.')}\n\n"
            texto += f"🎯 DIRETRIZES DO TURNO:\n"
            for meta in dados.get("metas_do_turno", []):
                texto += f"  [-] {meta}\n"
                
            self.txt_comandos_recebidos.insert(tk.END, texto)
        except Exception as e:
            self.txt_comandos_recebidos.insert(tk.END, f"Erro ao ler comandos do supervisor: {str(e)}")

    def cadastrar_novo_produto(self):
        pid = self.entry_cad_id.get().strip()
        nome = self.entry_cad_nome.get().strip()
        preco_txt = self.entry_cad_preco.get().strip()

        if not pid or not nome or not preco_txt:
            messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos do cadastro.")
            return

        if pid in self.banco_produtos:
            messagebox.showerror("Erro de ID", "Este Código ID já pertence a outro produto.")
            return

        try:
            preco = float(preco_txt.replace(",", "."))
        except ValueError:
            messagebox.showerror("Preço Inválido", "Digite um valor numérico válido para o preço.")
            return

        self.banco_produtos[pid] = {"nome": nome, "preco": preco, "lotes": {}}
        self.salvar_dados_locais()
        self.atualizar_tabela_lotes()
        
        self.entry_cad_id.delete(0, tk.END)
        self.entry_cad_nome.delete(0, tk.END)
        self.entry_cad_preco.delete(0, tk.END)
        messagebox.showinfo("Sucesso", f"'{nome}' pronto para receber lotes!")

    def processar_movimentacao(self):
        pid = self.entry_mov_id.get().strip()
        lote_nome = self.entry_mov_lote.get().strip().upper()
        qtd_txt = self.entry_mov_qtd.get().strip()
        val_txt = self.entry_mov_validade.get().strip()
        operacao = self.var_operacao.get()

        if not pid or not lote_nome or not qtd_txt:
            return

        if pid not in self.banco_produtos:
            messagebox.showwarning("Não Encontrado", "Código de produto não cadastrado.")
            return

        try:
            qtd = int(qtd_txt)
            if qtd <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Quantidade Inválida", "Insira um número inteiro válido.")
            return

        produto = self.banco_produtos[pid]

        if operacao == "Entrada":
            if not val_txt:
                messagebox.showwarning("Validade Requerida", "Para entradas, insira a validade (DD/MM/AAAA).")
                return
            try:
                datetime.strptime(val_txt, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Data Inválida", "Use o formato padrão correto: DD/MM/AAAA")
                return

            if lote_nome not in produto["lotes"]:
                produto["lotes"][lote_nome] = {"qtd": 0, "validade": val_txt}
            
            produto["lotes"][lote_nome]["qtd"] += qtd
            produto["lotes"][lote_nome]["validade"] = val_txt
        
        else:
            if lote_nome not in produto["lotes"]:
                messagebox.showwarning("Lote Inexistente", f"O lote '{lote_nome}' não existe para este produto.")
                return
            
            if produto["lotes"][lote_nome]["qtd"] >= qtd:
                produto["lotes"][lote_nome]["qtd"] -= qtd
                self.faturamento_dia += (produto["preco"] * qtd)
            else:
                messagebox.showwarning("Estoque Insuficiente", f"Lote com apenas {produto['lotes'][lote_nome]['qtd']} caixas.")
                return

            if produto["lotes"][lote_nome]["qtd"] == 0:
                del produto["lotes"][lote_nome]

        self.salvar_dados_locais()
        self.entry_mov_id.delete(0, tk.END)
        self.entry_mov_lote.delete(0, tk.END)
        self.entry_mov_qtd.delete(0, tk.END)
        self.entry_mov_validade.delete(0, tk.END)

        self.lbl_faturamento.configure(text=f"FATURAMENTO SESSÃO: R$ {self.faturamento_dia:,.2f}")
        self.atualizar_tabela_lotes()

    def atualizar_tabela_lotes(self):
        for widget in self.scroll_estoque.winfo_children():
            widget.destroy()

        headers = ["ID", "PRODUTO", "LOTE", "CAIXAS", "VALIDADE", "STATUS CRÍTICO"]
        larguras = [60, 200, 110, 100, 120, 180]

        frame_h = ctk.CTkFrame(self.scroll_estoque, fg_color="transparent")
        frame_h.pack(fill=tk.X, pady=5, padx=5)
        for h, l in zip(headers, larguras):
            ctk.CTkLabel(frame_h, text=h, font=("Segoe UI", 11, "bold"), text_color="#6e6e77", width=l, anchor="w").pack(side=tk.LEFT)

        nenhum_lote = True
        hoje = datetime.now()

        for pid, dados in self.banco_produtos.items():
            for lote_id, info in dados["lotes"].items():
                nenhum_lote = False
                linha = ctk.CTkFrame(self.scroll_estoque, height=40, fg_color="#18181c", corner_radius=8)
                linha.pack(fill=tk.X, pady=3, padx=5)
                linha.pack_propagate(False)

                try:
                    data_val = datetime.strptime(info["validade"], "%d/%m/%Y")
                    dias_restantes = (data_val - hoje).days
                except:
                    dias_restantes = 999

                if dias_restantes < 0:
                    st, cor = "❌ PRODUTO VENCIDO", "#e74c3c"
                elif dias_restantes <= 15:
                    st, cor = f"⚠️ CRÍTICO (VENCE EM {dias_restantes}D)", "#f39c12"
                elif info["qtd"] <= 50:
                    st, cor = "🚨 ESTOQUE BAIXO", "#e74c3c"
                else:
                    st, cor = "🟢 ESTÁVEL (OK)", "#2ecc71"

                ctk.CTkLabel(linha, text=pid, font=("Segoe UI", 12), text_color="#6e6e77", width=60, anchor="w").pack(side=tk.LEFT, padx=(5,0))
                ctk.CTkLabel(linha, text=dados["nome"], font=("Segoe UI", 12, "bold"), text_color="white", width=200, anchor="w").pack(side=tk.LEFT)
                ctk.CTkLabel(linha, text=lote_id, font=("Segoe UI", 11, "bold"), text_color="#3498db", width=110, anchor="w").pack(side=tk.LEFT)
                ctk.CTkLabel(linha, text=f"{info['qtd']} cx", font=("Segoe UI", 12, "bold"), text_color="white", width=100, anchor="w").pack(side=tk.LEFT)
                ctk.CTkLabel(linha, text=info["validade"], font=("Segoe UI", 12), text_color="#f1c40f", width=120, anchor="w").pack(side=tk.LEFT)
                ctk.CTkLabel(linha, text=st, font=("Segoe UI", 11, "bold"), text_color=cor, width=180, anchor="w").pack(side=tk.LEFT)

        if nenhum_lote:
            ctk.CTkLabel(self.scroll_estoque, text="Nenhum lote ativo no pátio.", font=("Segoe UI", 13, "italic"), text_color="#6e6e77").pack(pady=40)

    def exportar_para_supervisor(self):
        dados_exportacao = {
            "timestamp_envio": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "faturamento_da_sessao": self.faturamento_dia,
            "inventario_atualizado": self.banco_produtos
        }
        with open(self.arquivo_supervisor_saida, "w", encoding="utf-8") as f:
            json.dump(dados_exportacao, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Exportação", f"Fechamento exportado para o supervisor com sucesso!")

if __name__ == "__main__":
    app = GerenciadorEstoqueLotesAlmeida()
    app.mainloop()