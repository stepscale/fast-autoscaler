/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // By default, Docusaurus generates a sidebar from the docs folder structure
  mainSidebar: [
    'intro',
    'products',
    'about-us',
    'contact',
    {
      type: 'category',
      label: 'Fast Autoscaler',
      link: {
        type: 'doc',
        id: 'fast-autoscaler/intro',
      },
      items: [
        'fast-autoscaler/getting-started',
        'fast-autoscaler/configuration',
        {
          type: 'category',
          label: 'Concepts',
          items: [
            'fast-autoscaler/concepts/architecture',
            'fast-autoscaler/concepts/scaling-logic',
            'fast-autoscaler/concepts/state-management',
          ],
        },
        {
          type: 'category',
          label: 'Examples',
          items: [
            'fast-autoscaler/examples/basic-sqs',
            'fast-autoscaler/examples/high-frequency',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Articles',
      items: [
        'articles/why-fargate-instead-of-eks-ec2',
      ],
    },
  ],
};

export default sidebars;