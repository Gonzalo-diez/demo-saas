export type Category = {
  id: string;
  name: string;
  value: string;
  aliases?: string[];
  slug: string;
  description?: string;
  image_url?: string;
};

export const categories: Category[] = [
  {
    id: "cat-analgesicos",
    name: "Analgésicos y farmacia",
    value: "analgesicos",
    slug: "analgesicos-farmacia",
    aliases: ["analgesicos", "farmacia"],
    description: "Analgésicos, antiácidos, antigripales y productos básicos de botiquín.",
    image_url: "/images/categories/analgesicos.jpg",
  },
  {
    id: "cat-cigarrillos-economicos",
    name: "Cigarrillos económicos",
    value: "cigarrillos eco",
    slug: "cigarrillos-economicos",
    aliases: ["cigarrillos eco", "economicos"],
    description: "Marcas económicas de cigarrillos.",
    image_url: "/images/categories/economicos.jpg",
  },
  {
    id: "cat-cigarrillos-premium",
    name: "Cigarrillos Massalin y BAT",
    value: "masalin bat",
    slug: "cigarrillos-massalin-bat",
    aliases: ["masalin bat"],
    description: "Marcas Massalin, Philip Morris y BAT.",
    image_url: "/images/categories/maselin-bat.jpg",
  },
  {
    id: "cat-tabaco-accesorios",
    name: "Tabaco y accesorios",
    value: "tabaco accesorios",
    slug: "tabaco-accesorios",
    aliases: ["tabaco accesorios", "tabaco"],
    description: "Tabaco armado, papeles, filtros, celulosa y encendedores.",
    image_url: "/images/categories/tabaco-accesorios.jpg",
  },
  {
    id: "cat-pegamentos",
    name: "Pegamentos",
    value: "pegamentos",
    slug: "pegamentos",
    aliases: ["pegamentos", "pegamento"],
    description: "Pegamentos.",
    image_url: "/images/categories/pegamentos.jpg",
  },
  {
    id: "cat-pilas",
    name: "Pilas",
    value: "pilas",
    slug: "pilas",
    aliases: ["pilas", "pila"],
    description: "Pilas.",
    image_url: "/images/categories/pilas.jpg",
  },
  {
    id: "cat-preservativos",
    name: "Preservativos",
    value: "preservativos",
    slug: "preservativos",
    aliases: ["preservativos", "preservativo"],
    description: "Preservativos.",
    image_url: "/images/categories/preservativos.jpg",
  },
];