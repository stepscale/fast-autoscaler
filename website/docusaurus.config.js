// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import { themes as prismThemes } from 'prism-react-renderer';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'StepScale.io',
  tagline: 'Scale smarter, not harder',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://stepscale.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'stepscale', // Usually your GitHub org/user name.
  projectName: 'fast-autoscaler', // Usually your repo name.
  trailingSlash: false,
  deploymentBranch: 'gh-pages',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          routeBasePath: '/docs',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/stepscale-social-card.jpg',
      metadata: [
        { name: 'keywords', content: 'cloud scaling, autoscaling, infrastructure automation, aws, ecs, sqs, lambda, serverless, devops, stepscale' },
      ],
      navbar: {
        title: 'StepScale.io',
        logo: {
          alt: 'StepScale.io Logo',
          src: 'img/stepscale-logo.png',
        },
        items: [
          {
            to: '/',
            position: 'left',
            label: 'Home',
          },
          {
            to: '/docs/fast-autoscaler/intro',
            position: 'left',
            label: 'Fast Autoscaler',
            className: 'navbar-item-bold',
          },
          {
            to: '/docs/articles/intro',
            position: 'left',
            label: 'Articles',
          },
          {
            to: '/docs/about-us',
            position: 'left',
            label: 'About Us',
          },
          {
            to: '/docs/contact',
            position: 'left',
            label: 'Contact',
          },
          {
            href: 'https://github.com/stepscale/fast-autoscaler',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'yaml', 'json', 'python'],
      },
      colorMode: {
        defaultMode: 'light',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
    }),
};

export default config;