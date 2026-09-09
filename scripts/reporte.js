// Genera reporte/Reporte_Dashboard_Operativo.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, Footer, PageNumber, LevelFormat, convertInchesToTwip,
} = require("docx");

const RAIZ = path.resolve(__dirname, "..");
const SHOTS = path.join(RAIZ, "screenshots");

const ANCHO_TEXTO = 12240 - 2 * 1080; // Carta menos márgenes de 0.75"
const PX = 6.5 * 96;                  // ancho útil en px a 96 dpi

const AZUL = "1C5CAB";
const TINTA = "0B0B0B";
const GRIS = "52514E";
const GRIS_CLARO = "F0EFEC";

const p = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 120, line: 276 },
  alignment: o.align,
  children: [new TextRun({ text, size: o.size ?? 21, color: o.color ?? TINTA,
                           bold: o.bold, italics: o.italics, font: "Calibri" })],
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 280, after: 140 },
  children: [new TextRun({ text, size: 26, bold: true, color: AZUL, font: "Calibri" })],
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 200, after: 100 },
  children: [new TextRun({ text, size: 22, bold: true, color: TINTA, font: "Calibri" })],
});

function imagen(archivo, ratio, ancho = PX) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 60 },
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(path.join(SHOTS, archivo)),
      transformation: { width: Math.round(ancho), height: Math.round(ancho * ratio) },
    })],
  });
}

const pie = (text) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
  children: [new TextRun({ text, size: 17, italics: true, color: GRIS, font: "Calibri" })],
});

function tabla(encabezados, filas, anchos, derecha = false) {
  const celda = (txt, opts = {}) => new TableCell({
    width: { size: opts.w, type: WidthType.DXA },
    shading: opts.head ? { type: ShadingType.CLEAR, fill: GRIS_CLARO, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    children: [new Paragraph({
      spacing: { after: 0 },
      alignment: opts.right ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: [new TextRun({ text: txt, size: 19, bold: opts.head,
                               color: opts.head ? TINTA : GRIS, font: "Calibri" })],
    })],
  });

  return new Table({
    width: { size: ANCHO_TEXTO, type: WidthType.DXA },
    columnWidths: anchos,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "D9D8D2" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "D9D8D2" },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "E1E0D9" },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: [
      new TableRow({
        tableHeader: true,
        children: encabezados.map((t, i) => celda(t, { w: anchos[i], head: true, right: derecha && i === encabezados.length - 1 })),
      }),
      ...filas.map((f) => new TableRow({
        children: f.map((t, i) => celda(t, { w: anchos[i], right: derecha && i === f.length - 1 })),
      })),
    ],
  });
}

const doc = new Document({
  numbering: {
    config: [{
      reference: "vinetas",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.3), hanging: convertInchesToTwip(0.18) } } },
      }],
    }],
  },
  styles: { default: { document: { run: { font: "Calibri", size: 21, color: TINTA } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "Página ", size: 17, color: GRIS }),
                     new TextRun({ children: [PageNumber.CURRENT], size: 17, color: GRIS })],
        })],
      }),
    },
    children: [
      // ------------------------------------------------ Portada / encabezado
      new Paragraph({
        spacing: { after: 40 },
        children: [new TextRun({ text: "VISUALIZACIÓN DE DATOS · PRÁCTICA DE DASHBOARDS",
                                 size: 17, bold: true, color: AZUL, characterSpacing: 20 })],
      }),
      new Paragraph({
        spacing: { after: 60 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: AZUL, space: 6 } },
        children: [new TextRun({ text: "Dashboard Operativo de Producción", size: 34, bold: true, color: TINTA })],
      }),
      p("Nivel operativo · dirigido a supervisores de piso · indicadores de corto plazo (turno y día)",
        { color: GRIS, italics: true, after: 60 }),
      p("Fuente de datos: produccion.csv — 1 350 registros (90 días × 3 turnos × 5 líneas, "
        + "01/01/2023 a 31/03/2023). Herramienta: Python 3 con Dash y Plotly; diseño propio en CSS.",
        { color: GRIS, after: 200 }),

      // ------------------------------------------------ 1. Objetivo
      h1("1. Objetivo y alcance"),
      p("El tablero responde a la pregunta que un supervisor de línea se hace al arrancar o cerrar un "
        + "turno: ¿estamos cumpliendo el plan, con qué calidad y qué línea necesita atención ahora? "
        + "Por eso el horizonte es corto —turno, día y las últimas dos semanas— y la primera pantalla "
        + "no es una gráfica sino una lista de alertas accionables."),
      p("El dashboard es interactivo: los filtros de periodo, turno y línea recalculan los seis KPIs, "
        + "las seis gráficas, la tabla del último turno y las alertas en una sola operación."),

      // ------------------------------------------------ 2. Indicadores
      h1("2. Indicadores implementados"),
      p("Se implementaron seis KPIs derivados de las cuatro columnas numéricas del conjunto de datos. "
        + "Cada uno se compara contra su meta operativa y contra el periodo inmediato anterior de "
        + "igual duración, y se colorea con un semáforo de cuatro estados."),
      tabla(
        ["Indicador", "Fórmula", "Meta", "Valor (Q1)"],
        [
          ["Cumplimiento del plan", "Fabricado ÷ Planificado", "≥ 95 %", "93.4 %"],
          ["Unidades buenas", "Fabricado − Defectuosos", "—", "138 227 u"],
          ["Tasa de defectos (scrap)", "Defectuosos ÷ Fabricado", "≤ 3 %", "4.7 %"],
          ["Disponibilidad", "(480 − paro) ÷ 480 por turno", "≥ 90 %", "93.6 %"],
          ["OEE", "Disponibilidad × Rendimiento × Calidad", "≥ 85 %", "83.4 %"],
          ["Tiempo de paro", "Suma de TiempoParada_min", "≤ 45 min/turno", "41 143 min"],
        ],
        [3100, 3600, 1700, 1680], true,
      ),
      p("", { after: 60 }),
      p("Los umbrales del semáforo son: en meta (verde), atención (ámbar, hasta 5 puntos bajo meta), "
        + "riesgo (naranja, hasta 10 puntos) y crítico (rojo). El estado nunca se comunica solo con "
        + "color: cada marca lleva ícono y etiqueta de texto.", { color: GRIS }),
      imagen("03_kpis.png", 0.103),
      pie("Figura 1. Fila de KPIs con meta, variación respecto al periodo anterior y semáforo de estado."),

      // ------------------------------------------------ 3. Estructura
      h1("3. Estructura del dashboard"),
      p("El tablero se lee de arriba hacia abajo en tres niveles de detalle creciente: estado actual, "
        + "tendencia del periodo y desempeño por línea y turno."),

      h2("3.1 Estado actual: alertas y último turno"),
      p("Panel de alertas ordenadas por severidad (línea bajo plan, paro prolongado, scrap alto) y "
        + "tabla del último turno registrado con formato condicional. La columna Estado resume la peor "
        + "de las tres condiciones de cada línea: Línea-1 aparece como crítica pese a cumplir el plan "
        + "porque su scrap del turno llegó a 7 %."),
      imagen("04_alertas_y_turno.png", 0.306),
      pie("Figura 2. Alertas activas y detalle del turno del 31/03/2023 (Noche)."),

      h2("3.2 Tendencia del periodo"),
      p("Producción diaria contra el plan y porcentaje de cumplimiento día a día. Se usan dos gráficas "
        + "separadas en lugar de un doble eje: unidades y porcentaje no comparten escala."),
      imagen("05_tendencia.png", 0.267),
      pie("Figura 3. Producción diaria y cumplimiento del plan en los últimos 14 días."),

      h2("3.3 Desempeño por línea y turno"),
      p("Cumplimiento por línea (gráfica de puntos), mapa de calor de la tasa de defectos por línea y "
        + "turno, tiempo de paro acumulado y relación entre paro y cumplimiento."),
      imagen("06_detalle.png", 0.545),
      pie("Figura 4. Vista de detalle: las cuatro gráficas de diagnóstico."),

      // ------------------------------------------------ 4. Hallazgos
      h1("4. Hallazgos operativos"),
      new Paragraph({
        numbering: { reference: "vinetas", level: 0 }, spacing: { after: 100 },
        children: [new TextRun({ text: "El incumplimiento es estructural, no puntual: 87 de los 90 días quedaron bajo la meta de 95 %, con un promedio de 93.4 %. La brecha es de unas 10 184 unidades en el trimestre.", size: 21 })],
      }),
      new Paragraph({
        numbering: { reference: "vinetas", level: 0 }, spacing: { after: 100 },
        children: [new TextRun({ text: "La calidad es el cuello de botella real: el scrap promedio de 4.7 % supera en 1.7 puntos la meta de 3 % y es lo que arrastra el OEE (83.4 %) por debajo de su meta de 85 %, ya que la disponibilidad sí cumple (93.6 %).", size: 21 })],
      }),
      new Paragraph({
        numbering: { reference: "vinetas", level: 0 }, spacing: { after: 100 },
        children: [new TextRun({ text: "Ninguna línea ni turno se desmarca: el cumplimiento va de 93.0 % (Línea-1) a 93.6 % (Línea-5) y los tres turnos quedan entre 93.3 % y 93.6 %. El problema es del proceso completo, no de un equipo o una cuadrilla concretos.", size: 21 })],
      }),
      new Paragraph({
        numbering: { reference: "vinetas", level: 0 }, spacing: { after: 100 },
        children: [new TextRun({ text: "Los paros no explican el incumplimiento: la correlación entre minutos de paro y cumplimiento del turno es prácticamente nula (r = 0.02), como se ve en la nube de puntos de la Figura 4. La causa hay que buscarla en la velocidad de línea o en el propio dimensionamiento del plan, no en las detenciones.", size: 21 })],
      }),
      new Paragraph({
        numbering: { reference: "vinetas", level: 0 }, spacing: { after: 160 },
        children: [new TextRun({ text: "El valor diario del tablero está en el nivel de turno: aunque los promedios son planos, turnos individuales caen hasta 81.5 % de cumplimiento o 7 % de scrap. Ahí es donde las alertas dan una acción concreta al supervisor.", size: 21 })],
      }),

      // ------------------------------------------------ 5. Criterios de diseño
      h1("5. Criterios de diseño aplicados"),
      p("Las decisiones visuales siguen las buenas prácticas revisadas en clase: mostrar lo esencial, "
        + "usar color consistente con jerarquía visual y adaptar el tablero a su público."),
      tabla(
        ["Decisión", "Motivo"],
        [
          ["Un solo eje por gráfica", "Unidades y porcentajes se separan en dos gráficas en vez de un doble eje, que distorsiona la comparación."],
          ["Cumplimiento por línea como puntos, no barras", "Las diferencias son de décimas; una barra desde cero las volvería indistinguibles. Al no ser área, el eje puede recortarse sin engañar."],
          ["Color asignado por función", "Categórico para la identidad del turno, secuencial de un solo tono para el scrap y una paleta de estado reservada para el semáforo."],
          ["Etiqueta directa en cada celda y fila", "Ningún valor depende únicamente del color: el mapa de calor y la tabla muestran la cifra."],
          ["Ícono y texto junto a cada estado", "El tablero sigue siendo legible para daltonismo y en impresión a blanco y negro."],
          ["Alertas antes que gráficas", "El público objetivo son supervisores: la primera pantalla debe decir qué hacer, no describir el proceso."],
        ],
        [3400, 6680],
      ),

      h1("6. Cómo ejecutarlo"),
      p("Desde la carpeta del proyecto: crear el entorno virtual, instalar requirements.txt y ejecutar "
        + "python app.py; el dashboard queda en http://127.0.0.1:8050. En Windows basta con ejecutar "
        + "ejecutar.bat, que crea el entorno la primera vez. El detalle de la estructura de carpetas "
        + "está en README.md."),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const salida = path.join(RAIZ, "reporte", "Reporte_Dashboard_Operativo.docx");
  fs.writeFileSync(salida, buf);
  console.log("Escrito:", salida);
});
