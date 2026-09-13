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
    cdk.Tags.of(this).add('project', 'opendoor-relay');
    cdk.Tags.of(this).add('environment', stage);

    // DynamoDB Table
    const table = new dynamodb.Table(this, 'RelayTable', {
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    });

    // Lambda Function
    const backendFn = new lambda.Function(this, 'BackendFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
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
        SES_FROM_EMAIL: process.env.SES_FROM_EMAIL || 'areebamuhammad47@gmail.com',
      },
    });

    // Grant DynamoDB access strictly
    table.grantReadWriteData(backendFn);

    // Grant Bedrock access strictly
    backendFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
      resources: [
        `arn:aws:bedrock:${this.region}::foundation-model/*`,
        `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/*`
      ],
    }));

    // Grant SES access strictly
    backendFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['ses:SendEmail', 'ses:SendRawEmail'],
      resources: [
        `arn:aws:ses:${this.region}:${this.account}:identity/*`
      ],
    }));

    // Scheduler Role (Target Role)
    const schedulerRole = new iam.Role(this, 'SchedulerRole', {
      assumedBy: new iam.ServicePrincipal('scheduler.amazonaws.com'),
    });
    // The target role is restricted to invoking ONLY this specific Lambda
    backendFn.grantInvoke(schedulerRole);
    backendFn.addEnvironment('SCHEDULER_ROLE_ARN', schedulerRole.roleArn);

    // EventBridge Scheduler Policy for Lambda (Creation/Deletion)
    backendFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['scheduler:CreateSchedule', 'scheduler:DeleteSchedule', 'scheduler:GetSchedule'],
      resources: [`arn:aws:scheduler:${this.region}:${this.account}:schedule/default/*`],
    }));

    // PassRole restricted to the scheduler target role
    backendFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['iam:PassRole'],
      resources: [schedulerRole.roleArn],
    }));

    // API Gateway
    const api = new apigateway.LambdaRestApi(this, 'RelayApi', {
      handler: backendFn,
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
