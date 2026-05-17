import sys
import subprocess

# --- SISTEMA DE AUTO-INSTALAÇÃO DAS BIBLIOTECAS ---
try:
    import customtkinter as ctk
except ImportError:
    print("Instalando bibliotecas necessárias para a interface gráfica... Aguarde.")
    # Executa o pip install direto por dentro do processo do Python
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk

# Importação das outras bibliotecas nativas (já vêm com o Python)
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET
from datetime import datetime

# Configuração visual da interface moderna
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppAutomação(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Almeida Microautomações - Analisador Inteligente")
        self.geometry("700x550")
        
        # Variável para guardar os dados extraídos do XML da Nota Fiscal
        self.produtos_nota = []

        # --- CONTAINER PRINCIPAL (Para centralizar e organizar) ---
        self.titulo = ctk.CTkLabel(self, text="Sistema de Análise de Estoque e XML", font=ctk.CTkFont(size=20, weight="bold"))
        self.titulo.pack(pady=20)

        # --- SEÇÃO 1: LEITOR DE NOTA FISCAL (XML) ---
        self.frame_xml = ctk.CTkFrame(self)
        self.frame_xml.pack(fill="x", padx=20, pady=10)

        self.lbl_xml = ctk.CTkLabel(self.frame_xml, text="Leitor de Nota Fiscal Eletrônica (NF-e)", font=ctk.CTkFont(weight="bold"))
        self.lbl_xml.pack(anchor="w", padx=10, pady=5)

        self.btn_carregar_xml = ctk.CTkButton(self.frame_xml, text="Importar XML da Nota", command=self.carregar_xml)
        self.btn_carregar_xml.pack(pady=10)

        # --- SEÇÃO 2: ENTRADA DE DADOS E VALIDAÇÕES ---
        self.frame_dados = ctk.CTkFrame(self)
        self.frame_dados.pack(fill="x", padx=20, pady=10)

        # Inputs alinhados em grade (Grid)
        self.lbl_validade = ctk.CTkLabel(self.frame_dados, text="Data de Validade (DD/MM/AAAA):")
        self.lbl_validade.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_validade = ctk.CTkEntry(self.frame_dados, placeholder_text="Ex: 25/12/2026", width=200)
        self.entry_validade.grid(row=0, column=1, padx=10, pady=10)

        self.lbl_preco_b = ctk.CTkLabel(self.frame_dados, text="Preço do Distribuidor Concorrente (R$):")
        self.lbl_preco_b.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_preco_b = ctk.CTkEntry(self.frame_dados, placeholder_text="Ex: 15.50", width=200)
        self.entry_preco_b.grid(row=1, column=1, padx=10, pady=10)

        self.btn_analisar = ctk.CTkButton(self.frame_dados, text="Rodar Análise Completa", fg_color="green", hover_color="darkgreen", command=self.analisar_dados)
        self.btn_analisar.grid(row=2, column=0, columnspan=2, pady=15)

        # --- SEÇÃO 3: JANELA DE TEXTO DO RELATÓRIO ---
        self.txt_resultado = ctk.CTkTextbox(self, width=650, height=200, font=ctk.CTkFont(family="Courier", size=12))
        self.txt_resultado.pack(padx=20, pady=10)

    def carregar_xml(self):
        """Abre o gerenciador de arquivos do Windows para ler o XML da NF-e"""
        caminho_arquivo = filedialog.askopenfilename(filetypes=[("Arquivos XML", "*.xml")])
        if not caminho_arquivo:
            return

        try:
            tree = ET.parse(caminho_arquivo)
            root = tree.getroot()

            # Mapeamento do padrão de segurança de Namespaces da SEFAZ
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            self.produtos_nota = []
            self.txt_resultado.delete("1.0", tk.END)

            # Procura de forma segura pelas tags de detalhes de produtos (<det>)
            for det in root.findall('.//nfe:det', ns):
                prod_element = det.find('.//nfe:xProd', ns)
                preco_element = det.find('.//nfe:vUnCom', ns)
                
                if prod_element is not None and preco_element is not None:
                    nome_prod = prod_element.text
                    preco_unidade = float(preco_element.text)
                    self.produtos_nota.append({'nome': nome_prod, 'preco_a': preco_unidade})

            if self.produtos_nota:
                self.txt_resultado.insert(tk.END, f"✅ SUCESSO: Nota Fiscal carregada com êxito!\n")
                self.txt_resultado.insert(tk.END, f"Identificado(s) {len(self.produtos_nota)} produto(s) dentro do arquivo.\n")
                for p in self.produtos_nota:
                    self.txt_resultado.insert(tk.END, f"  -> {p['nome']}: R$ {p['preco_a']:.2f} (Fornecedor da Nota)\n")
            else:
                messagebox.showwarning("Aviso de Formato", "Não encontramos produtos estruturados no padrão esperado de NF-e.")

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao ler ou decodificar o arquivo XML:\n{e}")

    def analisar_dados(self):
        """Trata os erros de entrada e gera o cruzamento de inteligência de estoque"""
        if not self.produtos_nota:
            messagebox.showwarning("Ação Necessária", "Nenhum dado importado. Carregue o XML antes de rodar a análise.")
            return

        validade_txt = self.entry_validade.get().strip()
        preco_b_txt = self.entry_preco_b.get().strip()

        if not validade_txt or not preco_b_txt:
            messagebox.showwarning("Campos em Branco", "Preencha a data de validade e o preço do concorrente.")
            return

        try:
            # 1. Validação inteligente do formato da data informada
            partes_data = validade_txt.split('/')
            if len(partes_data) != 3:
                raise ValueError
            
            formato_ano = "%d/%m/%y" if len(partes_data[-1]) == 2 else "%d/%m/%Y"
            data_validade = datetime.strptime(validade_txt, formato_ano)
            data_atual = datetime.now()
            dias_restantes = (data_validade - data_atual).days

            # 2. Tratamento numérico do preço concorrente (aceita ponto ou vírgula)
            preco_b = float(preco_b_txt.replace(",", "."))

            # Limpeza do console visual e renderização do relatório final
            self.txt_resultado.delete("1.0", tk.END)
            self.txt_resultado.insert(tk.END, "================ RELATÓRIO INTELIGENTE DE ESTOQUE ================\n\n")
            
            # Bloco de decisão de validade
            if dias_restantes < 0:
                self.txt_resultado.insert(tk.END, f"🚨 PERIGO: O lote informado está VENCIDO há {abs(dias_restantes)} dias!\n\n")
            elif dias_restantes <= 30:
                self.txt_resultado.insert(tk.END, f"⚠️ ATENÇÃO: Restam apenas {dias_restantes} dias para vencer. Evite compras volumosas!\n\n")
            else:
                self.txt_resultado.insert(tk.END, f"✅ VALIDADE SEGURA: {dias_restantes} dias restantes até o vencimento.\n\n")

            self.txt_resultado.insert(tk.END, "ANÁLISE COMPARATIVA DE VALORES:\n")
            self.txt_resultado.insert(tk.END, "-" * 66 + "\n")
            
            # Varredura lógica automatizada de cada produto
            for p in self.produtos_nota:
                preco_a = p['preco_a']
                self.txt_resultado.insert(tk.END, f"Item: {p['nome']}\n")
                self.txt_resultado.insert(tk.END, f"  > Distribuidor A (XML): R$ {preco_a:.2f}  |  > Distribuidor B: R$ {preco_b:.2f}\n")
                
                if preco_a < preco_b:
                    diff = preco_b - preco_a
                    self.txt_resultado.insert(tk.END, f"  👉 COMPRA RECOMENDADA: Distribuidor A está R$ {diff:.2f} mais barato.\n")
                elif preco_b < preco_a:
                    diff = preco_a - preco_b
                    self.txt_resultado.insert(tk.END, f"  👉 COMPRA RECOMENDADA: Distribuidor B (Concorrente) economiza R$ {diff:.2f}.\n")
                else:
                    self.txt_resultado.insert(tk.END, "  👉 EMPATE FINANCEIRO: Os custos são iguais.\n")
                self.txt_resultado.insert(tk.END, "-" * 66 + "\n")

        except ValueError:
            messagebox.showerror("Erro de Formatação", "Preencha os dados corretamente:\n\n- Data: DD/MM/AAAA (Ex: 15/09/2026)\n- Preço: Use ponto ou vírgula (Ex: 14,90 ou 14.90)")

if __name__ == "__main__":
    app = AppAutomação()
    app.mainloop()