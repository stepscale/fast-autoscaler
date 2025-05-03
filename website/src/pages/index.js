import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';

import styles from './index.module.css';

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/fast-autoscaler/intro">
            Explore Fast Autoscaler
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Cloud-native scaling solutions`}
      description="StepScale.io provides cloud-native scaling solutions that evolve with your business. Our first product, Fast Autoscaler, optimizes AWS ECS services based on SQS queue metrics.">
      <HomepageHeader />
      <main>
        <section className={styles.section}>
          <div className="container">
            <div className="row">
              <div className="col col--8 col--offset-2">
                <h2 className={styles.sectionTitle}>About StepScale.io</h2>
                <p>
                  StepScale.io specializes in building intelligent scaling solutions for modern cloud infrastructure.
                  We help companies optimize their cloud resources, reduce operational costs, and improve system reliability
                  through advanced autoscaling technologies.
                </p>
                <p>
                  Our team brings together expertise in cloud infrastructure, serverless architectures, and software
                  engineering to create tools that simplify complex scaling challenges.
                </p>
              </div>
            </div>
          </div>
        </section>

        <HomepageFeatures />

        <section className={clsx(styles.section, styles.sectionAlt)}>
          <div className="container">
            <div className="row">
              <div className="col col--8 col--offset-2">
                <h2 className={styles.sectionTitle}>Our Products</h2>
                <div className={styles.productCard}>
                  <h3>Fast Autoscaler</h3>
                  <p>
                    A modular, extensible autoscaling solution for AWS ECS services based on queue metrics.
                    Fast Autoscaler dynamically adjusts your service's task count based on SQS queue depths
                    to optimize both performance and cost.
                  </p>
                  <div className={styles.buttonContainer}>
                    <Link className="button button--primary" to="/docs/fast-autoscaler/intro">
                      Learn More
                    </Link>
                    <Link className="button button--outline button--primary" to="https://github.com/stepscale/fast-autoscaler">
                      View on GitHub
                    </Link>
                  </div>
                </div>
                {/* Additional product cards can be added here as the company grows */}
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <div className="container">
            <div className="row">
              <div className="col col--8 col--offset-2 text--center">
                <h2 className={styles.sectionTitle}>Get Started Today</h2>
                <p>
                  Ready to optimize your cloud resources? Explore our documentation or contribute to our open source projects.
                </p>
                <div className={styles.buttonContainer}>
                  <Link className="button button--primary button--lg" to="/docs/intro">
                    Documentation
                  </Link>
                  <Link className="button button--secondary button--lg" to="/docs/contact">
                    Contact Us
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
} 