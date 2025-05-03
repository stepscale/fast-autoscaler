import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Intelligent Scaling',
    image: require('@site/static/img/feature-intelligent-scaling.png').default,
    description: (
      <>
        Dynamic resource allocation based on real-time metrics.
        Our solutions intelligently adjust resources to match workload demands.
      </>
    ),
  },
  {
    title: 'Cost Optimization',
    image: require('@site/static/img/feature-cost-optimization.png').default,
    description: (
      <>
        Scale resources up and down precisely when needed,
        eliminating waste and reducing cloud infrastructure costs.
      </>
    ),
  },
  {
    title: 'Open Source',
    image: require('@site/static/img/feature-open-source.png').default,
    description: (
      <>
        Our tools are open source and designed for extensibility.
        Contribute to our projects and help shape the future of cloud scaling.
      </>
    ),
  },
];


function Feature({ image, title, description }) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img className={styles.featureSvg} src={image} alt={title} />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}


export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}