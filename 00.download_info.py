import argparse
import random
from lxml import etree
import csv
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


# 提取基因详细信息
def extract_gene_info(gene_url):
    driver.get(gene_url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "li")))
    page_html = driver.page_source
    soup = BeautifulSoup(page_html, 'lxml')

    gene_info = {}

    # 提取基因相关信息
    gene_id = soup.find("strong", string="Gene ID:")
    if gene_id:
        gene_info["Gene ID"] = gene_id.find_next("a").text.strip()

    gene_symbol = soup.find("strong", string="Gene Symbol:")
    if gene_symbol:
        gene_info["Gene Symbol"] = gene_symbol.find_next("u").text.strip()

    gene_name_strong = soup.find("strong", string="Gene Name:")
    if gene_name_strong:
        # 获取包含 "Gene Name:" 的 <strong> 标签所在的 <li> 标签
        gene_name_li = gene_name_strong.find_parent("li")
        if gene_name_li:
            # 从 <li> 标签中提取文本
            next_text = gene_name_li.text.strip().split(":", 1)[-1].strip()
            gene_info["Gene Name"] = next_text if next_text else "Gene Name Not Available"

    genome = soup.find("strong", string="Genome:")
    if genome:
        gene_info["Genome"] = genome.find_next("a").text.strip()

    species = soup.find("strong", string="Species:")
    if species:
        gene_info["Species"] = species.find_next("em").text.strip()

    # 提取功能描述
    functional_descriptions = soup.find(id="functional-descriptions")
    if functional_descriptions:
        func_desc_list = functional_descriptions.find_next("ul").find_all("li")
        gene_info["Functional Descriptions"] = [desc.text.strip() for desc in func_desc_list]

    Function = soup.find(id="function-related-keywords")
    if Function:
        func_key_list = Function.find_next("ul").find_all("a")
        gene_info["function-related-keywords"] = [desc.text.strip() for desc in func_key_list]

    Literature = soup.find(id="literature")
    if Literature:
        lite_list = Literature.find_next("ul").find_all("a")
        gene_info["literature"] = [desc.text.strip() for desc in lite_list]

    # Related News
    related_news = soup.find(id="related-news")
    if related_news:
        gene_info["Related News"] = related_news.find_next("ul").find_all("h2")

    # Gene Resources (NCBI ID, UniProt accessions)
    gene_resources = soup.find(id="gene-resources")
    if gene_resources:
        gene_info["NCBI ID"] = gene_resources.find_next("a", href=lambda
            href: href and "ncbi.nlm.nih.gov" in href).text.strip()
        gene_info["UniProt accessions"] = gene_resources.find_next("a", href=lambda
            href: href and "uniprot.org" in href).text.strip()

    # Orthologs
    orthologs = soup.find(id="orthologs")
    if orthologs:
        ortholog_list = orthologs.find_next("ul").find_all("h2")
        gene_info["Orthologs"] = [orth.text.strip() for orth in ortholog_list]

    # Sequences
    sequences = soup.find(id="sequences")
    if sequences:
        cds_sequence = sequences.find_next("strong", string=lambda text: text and "CDS Sequence" in text)
        protein_sequence = sequences.find_next("strong", string=lambda text: text and "Protein Sequence" in text)
        if cds_sequence:
            gene_info["CDS Sequence"] = cds_sequence.text.strip()
        if protein_sequence:
            gene_info["Protein Sequence"] = protein_sequence.text.strip()

    return gene_info


# 主函数，爬取基因卡片信息并保存到文件
def scrape_gene_cards():
    # 设置 Selenium WebDriver 配置
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 模拟正常用户
    global driver
    driver = webdriver.Chrome(options=options)

    all_gene_info = []

    try:
        # 打开包含基因卡片的网页
        driver.get("https://funplantgenes.wiki/categories/triticum-aestivum/page/2/")  # 替换为实际的网页地址

        # 等待页面加载并定位卡片元素
        wait = WebDriverWait(driver, 10)
        cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card")))

        # 遍历每一个卡片并提取标题和链接
        card_info= {}
        for card in cards:
            try:
                # 尝试获取标题
                title_element = card.find_element(By.CLASS_NAME, "card-title")
                title = title_element.text if title_element else "未找到标题"  # 如果没有找到，则显示未找到标题

                # 获取 href 链接
                href = card.get_attribute("href")
                card_info[title]=href
            except Exception as e:
                print(f"处理卡片时出错: {e}")
                continue
        #print(card_info)

        for k,v in card_info.items():
            try:
                title = k
                href = v
                print(f"访问 {title} 的链接: {href}")

                # 访问每个基因的详细页面并提取信息
                gene_info = extract_gene_info(href)
                gene_info["Title"] = title  # 添加标题信息
                all_gene_info.append(gene_info)
                print(len(all_gene_info))
                print(gene_info)

                time.sleep(5)  # 为了避免频繁请求，添加延时

            except Exception as e:
                print(f"访问链接时出错: {e}")

    finally:
        driver.quit()
        # 保存到文件
    file_name = "gene_info_output2.tsv"
    # 在写入数据前，确保每个字典都有一致的字段名

    all_fields = set()
    for gene_info in all_gene_info:
        all_fields.update(gene_info.keys())

    # 确保每个字典都包含所有字段，并补齐缺失的字段
    for gene_info in all_gene_info:
        for field in all_fields:
            if field not in gene_info:
                gene_info[field] = None  # 缺失的字段值设为 None

    # 将数据写入文件
    with open(file_name, 'w', newline='', encoding='utf-8') as file:
        # 使用 DictWriter 写入字典
        writer = csv.DictWriter(file, delimiter='\t', fieldnames=all_fields)
        writer.writeheader()
        writer.writerows(all_gene_info)

    print(f"所有基因信息已保存到 {file_name}")


if __name__ == "__main__":
    scrape_gene_cards()

############################################分步
# options = webdriver.ChromeOptions()
# options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 模拟正常用户
# global driver
# driver = webdriver.Chrome(options=options)
#
# driver.get("https://funplantgenes.wiki/genes/2024.6.9/triticum-aestivum/solyc02g069260/")
# #time.sleep(10)  # 等待页面加载
# WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "li")))
# page_html = driver.page_source
# soup = BeautifulSoup(page_html, 'lxml')
#
# # 提取基因相关信息
# gene_info = {}
# gene_id = soup.find("strong", string="Gene ID:")
# if gene_id:
#     gene_info["Gene ID"] = gene_id.find_next("a").text.strip()
#
# gene_symbol = soup.find("strong", string="Gene Symbol:")
# if gene_symbol:
#     gene_info["Gene Symbol"] = gene_symbol.find_next("u").text.strip()
# gene_name = soup.find("li", string=lambda text: text and "Gene Name" in text)
# genome = soup.find("strong", string="Genome:")
# if genome:
#     gene_info["Genome"] = genome.find_next("a").text.strip()
# species = soup.find("strong", string="Species:")
# if species:
#     gene_info["Species"] = species.find_next("em").text.strip()
# print(gene_id)
# # 解析具体的内容
# if gene_name:
#     gene_info["Gene Name"] = gene_name.text.strip().split(":")[-1].strip()
#
#
# # 提取功能描述
# functional_descriptions = soup.find(id="functional-descriptions")
# if functional_descriptions:
#     func_desc_list = functional_descriptions.find_next("ul").find_all("li")
#     gene_info["Functional Descriptions"] = [desc.text.strip() for desc in func_desc_list]
#
# Function = soup.find(id="function-related-keywords")
# if Function:
#     func_key_list = Function.find_next("ul").find_all("a")
#     gene_info["function-related-keywords"] = [desc.text.strip() for desc in func_key_list]
#
# Literature = soup.find(id="literature")
# if Literature:
#     lite_list = Literature.find_next("ul").find_all("a")
#     gene_info["literature"] = [desc.text.strip() for desc in lite_list]
#
# # Related News
# related_news = soup.find(id="related-news")
# if related_news:
#     gene_info["Related News"] = related_news.find_next("ul").find_all("h2")
#
# # Gene Resources (NCBI ID, UniProt accessions)
# gene_resources = soup.find(id="gene-resources")
# if gene_resources:
#     gene_info["NCBI ID"] = gene_resources.find_next("a", href=lambda href: href and "ncbi.nlm.nih.gov" in href).text.strip()
#     gene_info["UniProt accessions"] = gene_resources.find_next("a", href=lambda href: href and "uniprot.org" in href).text.strip()
#
# # Orthologs
# orthologs = soup.find(id="orthologs")
# if orthologs:
#     ortholog_list = orthologs.find_next("ul").find_all("h2")
#     gene_info["Orthologs"] = [orth.text.strip() for orth in ortholog_list]
#
# # Sequences
# sequences = soup.find(id="sequences")
# if sequences:
#     cds_sequence = sequences.find_next("strong", string=lambda text: text and "CDS Sequence" in text)
#     protein_sequence = sequences.find_next("strong", string=lambda text: text and "Protein Sequence" in text)
#     if cds_sequence:
#         gene_info["CDS Sequence"] = cds_sequence.text.strip()
#     if protein_sequence:
#         gene_info["Protein Sequence"] = protein_sequence.text.strip()
#
# # 输出或处理提取的信息
# print(gene_info)
#
# driver.quit()