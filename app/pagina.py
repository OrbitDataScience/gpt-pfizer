import streamlit as st
import pandas as pd
import asyncio
import re
import openai
import aiohttp


# Função para classificar o comentário com base em uma única pergunta
async def classificar_comentario(session, comentario, pergunta, prompt, categoria):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "application/json"
    }
    
    # Prompt que analisa o comentário e responde à pergunta
    prompt = f"Você vai analisar o seguinte comentário: '{comentario}'. Responda à seguinte pergunta com '1' para Sim ou '0' para Não:\n- {pergunta}\n"
    
    data = {
        "model": "gpt-4o", 
        "messages": [
            {"role": "system", "content": (
                """Leia o comentário e identifique se ele está relacionado à categoria: {categoria}. 
                   Essa categoria pode incluir opiniões e dúvidas sobre o papel da mídia, das redes sociais e dos influenciadores na comunicação sobre vacinas, com ênfase nos pontos:
                   Influência e confiança na mídia e influenciadores: opiniões sobre a credibilidade da mídia e dos influenciadores na promoção das vacinas, incluindo críticas sobre ocultação de informações ou tendências na divulgação de dados.
                   Disseminação de informações incorretas: preocupações sobre a propagação de fake news ou a falta de transparência em relação aos efeitos das vacinas.
                   Foco ou ausência de cobertura midiática: comentários que mencionam a falta de cobertura de certos temas relacionados à vacinação (como COVID-19 ou vacinas específicas) ou percebem a mídia como alarmista."""
            )},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0  # Temperatura mais baixa para respostas mais consistentes
    }

    async with session.post(url, headers=headers, json=data) as response:
        result = await response.json()
        
        if 'choices' in result and result['choices']:
            resposta = result['choices'][0]['message']['content'].strip()
            
            # Verifica se a resposta é "1" ou "0"
            if resposta == "1":
                return 1
            elif resposta == "0":
                return 0
            else:
                return None
        else:
            print("Erro: Estrutura inesperada na resposta da API", result)
            return None  # Retorna None em caso de erro


async def processar_planilha(arquivo_excel, categoria, prompt):
    # Carrega o arquivo Excel
    df = pd.read_excel(arquivo_excel)

    # Colunas de perguntas (exceto a primeira coluna que contém o texto)
    df.columns[2] = categoria
    perguntas = df.columns[2:]
    
    async with aiohttp.ClientSession() as session:
        # Itera sobre cada linha de comentário
        for index, row in df.iterrows():
            comentario = row['Texto']  # O comentário a ser analisado
            
            # Itera sobre cada pergunta para o comentário atual
            for pergunta in perguntas:
                resposta = await classificar_comentario(session, comentario, pergunta, prompt, categoria)
                
                if resposta is not None:
                    df.at[index, pergunta] = resposta
                else:
                    print(f"Erro ao processar a pergunta '{pergunta}' para o comentário na linha {index}")

    # Salva o DataFrame com os resultados em um novo arquivo Excel
    df.to_excel('result.xlsx', index=False)
    st.dataframe(df)    
    st.write(f"Processo concluído e salvo no arquivo 'result.xlsx'")

# Função Principal
def main():
    st.set_page_config(page_title="Orbit AI", layout='wide')
    
    #SIDEBAR
    with st.sidebar:
        st.header('GPT Classifier Pfizer')
        uploaded_file = st.file_uploader("Faça o upload do arquivo Excel com os comentários", type="xlsx", help="O arquivo deve conter uma coluna chamada 'Texto'.", accept_multiple_files=False)
        prompt = st.text_area("Insira o prompt de comando")
        categoria = st.chat_input("Insira a categoria da análise")
    
    #MAIN
    if uploaded_file is not None and prompt is not None and categoria is not None:
        asyncio.run(processar_planilha(arquivo_excel, categoria, prompt))
    else:
        st.info("Faça o upload de um arquivo Excel e insira o prompt para começar.")

if __name__ == '__main__':
    main()