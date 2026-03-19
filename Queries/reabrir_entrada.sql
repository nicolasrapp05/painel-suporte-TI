set @existeEntrada = (select pceentradas.codpceentradas from pceentradas where pceentradas.codpceentradas = @codpceentrada);


set @temfinbaixado = (select 
							 if(INSTR(group_concat(if(creddebi.codbaixa = 0, "False","True")),"True") > 0,"True","False") as baixa from creddebi
							 where creddebi.chavecodigo = @codpceentrada and creddebi.chavereferencia = "pceentradas" and creddebi.chavereferenciaqual = "PCEEntrada");
							 
set @confirmacomfinanceiro = "False";

set @temsaida = (select 
					  if(instr(group_concat(if(pceentradasitensdetalhessaidas.sa_codigo >0,"True","False")),"True") > 0,"True","False") as teste
                 from pceentradasitensdetalhessaidas 
                 left join pceentradas on pceentradas.codpceentradas = pceentradasitensdetalhessaidas.codpceentradas
					  where pceentradasitensdetalhessaidas.codpceentradas = @codpceentrada
					  and pceentradas.gerasaida = "True");

set @confirmacomsaida = "True";

delete from movimentocorrente 
where movimentocorrente.codcreddebi in(select creddebi.codcreddebi from creddebi where chavecodigo = @codpceentrada and chavereferencia = "pceentradas" and chavereferenciaqual = "PCEEntrada")
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));


insert into logsistema(nomeusuario,datahora,descricao)
select
funcionarios.fu_login,
now(),
concat("Excluiu Financeiro por Reabertura de Entrada de Material: ",creddebi.codcreddebi) as descricao
from creddebi
left join funcionarios on funcionarios.fu_codigo = @codfuncionario
where creddebi.chavecodigo = @codpceentrada and creddebi.chavereferencia = "pceentradas" and creddebi.chavereferenciaqual = "PCEEntrada"
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"))
having not isnull(fu_login);

insert into creddebiex
select * from creddebi 
where creddebi.chavecodigo = @codpceentrada and creddebi.chavereferencia = "pceentradas" and creddebi.chavereferenciaqual = "PCEEntrada"
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));

delete from creddebi
where creddebi.chavecodigo = @codpceentrada and creddebi.chavereferencia = "pceentradas" and creddebi.chavereferenciaqual = "PCEEntrada"
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));

set @codsaida = (select pceentradasitensdetalhessaidas.sa_codigo 
					  from pceentradasitensdetalhessaidas 
					  left join pceentradas on pceentradas.codpceentradas = pceentradasitensdetalhessaidas.codpceentradas
					  where pceentradasitensdetalhessaidas.codpceentradas = @codpceentrada and pceentradas.gerasaida = 'True'
					  and pceentradasitensdetalhessaidas.sa_codigo <> 0
					  group by pceentradasitensdetalhessaidas.codpceentradas);

update itenssaidas
set itenssaidas.itsa_quantidader = itenssaidas.itsa_quantidade
where itenssaidas.itsa_saida = @codsaida
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));

update saidas
set saidas.sa_status2 = "True"
where saidas.sa_codigo = @codsaida
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));

insert into produtoshistoricos(codproduto,data,historico,usinclusao,dthrinclusao,valor,referenciatabela,referenciacampo,referenciacodigo,qtd,estoqueatual)
select
itenssaidas.itsa_produto,
curdate() as 'data',
'Entrada Materiais - Retorno Devolvel' as 'historico',
(select cast(funcionarios.fu_codigo as char) from funcionarios where funcionarios.fu_codigo = @codfuncionario) as 'usinclusao',
concat(curdate(), ' ', curtime()) as 'dthrinclusao',
itenssaidas.itsa_valor as 'valor',
'pceentradas' as 'referenciatabela',
'codpceentrada' as 'referenciacampo',
@codpceentrada as 'referenciacodigo',
itenssaidas.itsa_quantidader as 'qtd',
produtos.pr_qtdestoque + itenssaidas.itsa_quantidader as 'estoqueatual'
from itenssaidas
inner join produtos on produtos.pr_codigo = itenssaidas.itsa_produto
where itenssaidas.itsa_saida = @codsaida
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));

update produtos
inner join itenssaidas on itenssaidas.itsa_produto = produtos.pr_codigo
set produtos.pr_qtdestoque = produtos.pr_qtdestoque + itenssaidas.itsa_quantidader
where itenssaidas.itsa_saida =  @codsaida
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));

insert into produtoshistoricos(codproduto,data,historico,usinclusao,dthrinclusao,valor,referenciatabela,referenciacampo,referenciacodigo,qtd,estoqueatual)
select
pceentradasitens.codproduto,
curdate() as 'data',
'Entrada - Reabriu' as 'historico',
(select cast(funcionarios.fu_codigo as char) from funcionarios where funcionarios.fu_codigo = @codfuncionario) as 'usinclusao',
concat(curdate(), ' ', curtime()) as 'dthrinclusao',
pceentradasitens.valorunitario as 'valor',
'pceentrada' as 'referenciatabela',
'codpceentradas' as 'referenciacampo',
@codpceentrada as 'referenciacodigo',
pceentradasitensdetalhes.quantidade * (-1) as 'qtd',
produtos.pr_qtdestoque - pceentradasitensdetalhes.quantidade as 'estoqueatual'
from pceentradasitens
inner join produtos on produtos.pr_codigo = pceentradasitens.codproduto
inner join pceentradasitensdetalhes on pceentradasitensdetalhes.codpceentradasitens = pceentradasitens.codpceentradasitens
where pceentradasitens.codpceentradas = @codpceentrada and pceentradasitensdetalhes.quantidade <> 0
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));

update produtos 
inner join pceentradasitens on pceentradasitens.codproduto = produtos.pr_codigo
inner join pceentradasitensdetalhes on pceentradasitensdetalhes.codpceentradasitens = pceentradasitens.codpceentradasitens
set produtos.pr_qtdestoque = produtos.pr_qtdestoque - pceentradasitensdetalhes.quantidade
where produtos.pr_codigo in(select pceentradasitens.codproduto from pceentradasitens where pceentradasitens.codpceentradas = @codpceentrada)
and pceentradasitens.codpceentradas = @codpceentrada and pceentradasitensdetalhes.quantidade <> 0
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));

update pceentradas
set pceentradas.status = 'False'
where pceentradas.codpceentradas = @codpceentrada
and (@temfinbaixado = "False" or (@temfinbaixado = "True" and @confirmacomfinanceiro = "True"))
and (@temsaida = "False" or(@temsaida = "True" and @confirmacomsaida = "True"));




select 
if(isnull(@existeEntrada),
	"Entrada Nao Encontrada",
	if(@temfinbaixado = "True" and @confirmacomfinanceiro = "False",
		if(@temsaida = "True" and @confirmacomsaida = "False",
			concat("Atenção!!! Entrada com Financeiro e Saida Marcada \n","Para Confirmar a Reabertura informe 'True' na Confirmacomfinanceiro e Confirmacomsaida"),
			concat("Atenção Tem Financeiro Baixado !!! \n","Para Reabrir Informe 'True' no confirmacomfinanceiro")),
		
		if(@temsaida = "True" and @confirmacomsaida = "False",
			concat("Atenção tem Saida de Material!!! \n", "Para Reabrir informe 'True' no confirmacomsaida"),
			"Entrada Reaberta!!!"))
 ) as Cofirmação