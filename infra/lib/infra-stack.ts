import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as path from 'path';

export interface OpenDoorRelayStackProps extends cdk.StackProps {
  stage?: string;
}

export class OpenDoorRelayStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: OpenDoorRelayStackProps = {}) {
    super(scope, id, props);

    const stage = props.stage || 'hackathon';
    const sesFromEmail = process.env.SES_FROM_EMAIL?.trim();
    if (!sesFromEmail) {
      throw new Error('SES_FROM_EMAIL must be set to an SES-verified identity before synth or deploy');
    }

    cdk.Tags.of(this).add('project', 'opendoor-relay');
    cdk.Tags.of(this).add('environment', stage);

    const table = new dynamodb.Table(this, 'RelayTable', {
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    });

    const backendFn = new lambda.Function(this, 'BackendFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.X86_64,
      handler: 'opendoor_relay.api.app.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '..', 'backend.zip')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      reservedConcurrentExecutions: 5,
      logRetention: logs.RetentionDays.ONE_WEEK,
      environment: {
        DYNAMODB_TABLE_NAME: table.tableName,
        ENVIRONMENT: stage,
        AGENT_MODE: 'rehearsal',
        AGENTCORE_STATUS: 'NOT_DEPLOYED',
        BEDROCK_MODEL_ID: process.env.BEDROCK_MODEL_ID || 'us.amazon.nova-micro-v1:0',
        SES_FROM_EMAIL: sesFromEmail,
        PUBLIC_APP_URL: process.env.PUBLIC_APP_URL || 'http://localhost:5173',
      },
    });

    table.grantReadWriteData(backendFn);

    // Rehearsal mode does not receive Bedrock permissions. Add exact model/profile
    // ARNs only when live Bedrock is deliberately enabled in a later deployment.

    backendFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['ses:SendEmail', 'ses:SendRawEmail'],
      resources: [
        cdk.Stack.of(this).formatArn({
          service: 'ses',
          resource: 'identity',
          resourceName: sesFromEmail,
        }),
      ],
    }));

    const schedulerRole = new iam.Role(this, 'SchedulerRole', {
      assumedBy: new iam.ServicePrincipal('scheduler.amazonaws.com'),
    });
    backendFn.grantInvoke(schedulerRole);
    backendFn.addEnvironment('SCHEDULER_ROLE_ARN', schedulerRole.roleArn);

    backendFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['scheduler:CreateSchedule', 'scheduler:DeleteSchedule', 'scheduler:GetSchedule'],
      resources: [`arn:${cdk.Aws.PARTITION}:scheduler:${this.region}:${this.account}:schedule/default/*`],
    }));

    backendFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['iam:PassRole'],
      resources: [schedulerRole.roleArn],
      conditions: {
        StringEquals: {
          'iam:PassedToService': 'scheduler.amazonaws.com',
        },
      },
    }));

    const api = new apigateway.LambdaRestApi(this, 'RelayApi', {
      handler: backendFn,
      endpointTypes: [apigateway.EndpointType.REGIONAL],
      deployOptions: {
        throttlingRateLimit: 10,
        throttlingBurstLimit: 5,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: ['http://localhost:5173', 'http://127.0.0.1:5173'],
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
    });

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'Temporary AWS-hosted fallback API while live Bedrock and AgentCore proof remain pending.',
    });
  }
}
