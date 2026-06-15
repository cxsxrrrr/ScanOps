"""Views for accounts app."""
import logging

from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import stripe

stripe.api_version = '2026-05-27.dahlia'

from .models import User, Organization, Invitation, PLAN_MEMBER_LIMITS
from .serializers import UserSerializer, ProfileSerializer, OrganizationSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    Verify Clerk token and return user data.
    The ClerkJWTAuthentication backend auto-creates users,
    so if we reach here, the user is already authenticated.
    """
    serializer = ProfileSerializer(request.user)
    return Response({
        'user': serializer.data,
        'is_new': request.user.organization is None,
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get or update user profile."""
    if request.method == 'GET':
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    serializer = UserSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(ProfileSerializer(request.user).data)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def organization_detail(request):
    """Get or update user's organization."""
    if not request.user.organization:
        # Auto-create organization if it doesn't exist to prevent 404s and 
        # allow checkout sessions to work immediately.
        name = request.data.get('name') if request.method == 'PATCH' else f"Org de {request.user.first_name or request.user.username}"
        if not name:
            name = f"Org de {request.user.email}"
            
        org = Organization.objects.create(name=name, plan='free', url_limit=1)
        request.user.organization = org
        request.user.save(update_fields=['organization'])
        
        if request.method == 'GET':
            return Response(OrganizationSerializer(org).data)
        return Response(OrganizationSerializer(org).data, status=status.HTTP_201_CREATED)

    if request.method == 'GET':
        serializer = OrganizationSerializer(request.user.organization)
        return Response(serializer.data)

    serializer = OrganizationSerializer(
        request.user.organization, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_terms(request):
    """Record that the user has accepted the terms and conditions."""
    user = request.user
    if user.has_accepted_terms:
        return Response({
            'detail': 'Terms already accepted.',
            'accepted_terms_at': user.accepted_terms_at,
        })

    user.accept_terms()
    return Response({
        'detail': 'Terms accepted successfully.',
        'accepted_terms_at': user.accepted_terms_at,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team_list(request):
    """List team members in the user's organization."""
    org = request.user.organization
    if not org:
        return Response([], status=200)
    members = org.users.select_related('organization').values(
        'id', 'email', 'first_name', 'last_name', 'role'
    )
    return Response(list(members))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def invitation_list(request):
    """List or create invitations for the user's organization."""
    org = request.user.organization
    if not org:
        return Response({'detail': 'No organization.'}, status=400)

    if request.method == 'GET':
        invitations = Invitation.objects.filter(
            organization=org, accepted_by__isnull=True
        ).select_related('created_by').values(
            'id', 'token', 'created_at', 'created_by__email'
        )
        result = []
        for inv in invitations:
            result.append({
                'id': inv['id'],
                'token': str(inv['token']),
                'created_at': inv['created_at'],
                'created_by__email': inv['created_by__email'],
                'uses': 0,
                'max_uses': 1,
                'is_valid': True,
            })
        return Response(result)

    # POST: create invitation
    member_count = org.users.count()
    member_limit = PLAN_MEMBER_LIMITS.get(org.plan, 1)
    if member_count >= member_limit:
        return Response(
            {'detail': f'Limite de miembros alcanzado ({member_limit}). Mejora tu plan.'},
            status=400,
        )

    invitation = Invitation.objects.create(
        organization=org, created_by=request.user
    )
    return Response({
        'id': invitation.id,
        'token': str(invitation.token),
        'created_at': invitation.created_at,
        'uses': 0,
        'max_uses': 1,
        'is_valid': True,
    }, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revoke_invitation(request, invitation_id):
    """Revoke a pending invitation."""
    org = request.user.organization
    try:
        invitation = Invitation.objects.get(
            id=invitation_id, organization=org, accepted_by__isnull=True
        )
        invitation.delete()
        return Response({'detail': 'Invitacion revocada.'})
    except Invitation.DoesNotExist:
        return Response({'detail': 'Invitacion no encontrada.'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def invitation_info(request, token):
    """Get invitation info by token (public, no auth needed)."""
    try:
        invitation = Invitation.objects.select_related('organization', 'created_by').get(
            token=token, accepted_by__isnull=True
        )
        org = invitation.organization
        member_limit = PLAN_MEMBER_LIMITS.get(org.plan, 1)
        return Response({
            'id': invitation.id,
            'token': str(invitation.token),
            'organization_name': org.name,
            'organization_plan': org.plan,
            'member_count': org.users.count(),
            'member_limit': member_limit,
            'created_by_email': invitation.created_by.email,
            'created_at': invitation.created_at,
        })
    except Invitation.DoesNotExist:
        return Response(
            {'detail': 'Invitacion invalida o ya aceptada.'}, status=404
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invitation(request, token):
    """Accept an invitation and join the organization."""
    try:
        invitation = Invitation.objects.select_related('organization').get(
            token=token, accepted_by__isnull=True
        )
    except Invitation.DoesNotExist:
        return Response(
            {'detail': 'Invitacion invalida o ya aceptada.'}, status=404
        )

    org = invitation.organization
    member_count = org.users.count()
    member_limit = PLAN_MEMBER_LIMITS.get(org.plan, 1)
    if member_count >= member_limit:
        return Response(
            {'detail': f'Limite de miembros alcanzado en esta organizacion ({member_limit}).'},
            status=400,
        )

    if request.user.organization and request.user.organization != org:
        return Response(
            {'detail': 'Ya perteneces a otra organizacion. Sal de ella primero.'},
            status=400,
        )

    request.user.organization = org
    if request.data.get('first_name'):
        request.user.first_name = request.data['first_name']
    if request.data.get('last_name'):
        request.user.last_name = request.data['last_name']
    request.user.save(update_fields=['organization', 'first_name', 'last_name'])

    invitation.accepted_by = request.user
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=['accepted_by', 'accepted_at'])

    return Response({
        'detail': f'Te has unido a {org.name}.',
        'organization': OrganizationSerializer(org).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_organization(request):
    """Leave the current organization."""
    user = request.user
    if not user.organization:
        return Response({'detail': 'No perteneces a ninguna organizacion.'}, status=400)

    user.organization = None
    user.save(update_fields=['organization'])
    return Response({'detail': 'Has salido de la organizacion.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """Create a Stripe Checkout Session for subscription upgrade."""
    org = request.user.organization
    if not org:
        return Response({'detail': 'No organization.'}, status=400)

    plan = request.data.get('plan')
    if plan not in ['pro', 'ultimate']:
        return Response({'detail': 'Plan invalido.'}, status=400)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # We should define Stripe Prices in environment or here for simplicity
    # For now, let's assume we map the plan to a generic price ID or just pass product data.
    # To use Billing (Subscriptions), we MUST use a real price_id from the Stripe dashboard.
    # If the user hasn't created prices, we can't fully create a subscription session without it.
    # But for this implementation, we will use price IDs passed from frontend or mapped.
    # Best practice is mapping them from env.
    
    price_id = None
    if plan == 'pro' and hasattr(settings, 'STRIPE_PRICE_PRO') and settings.STRIPE_PRICE_PRO:
        price_id = settings.STRIPE_PRICE_PRO
    elif plan == 'ultimate' and hasattr(settings, 'STRIPE_PRICE_ULTIMATE') and settings.STRIPE_PRICE_ULTIMATE:
        price_id = settings.STRIPE_PRICE_ULTIMATE

    if price_id:
        line_item = {
            'price': price_id,
            'quantity': 1,
        }
    else:
        # Fallback to ad-hoc dynamic price if they are not defined yet in .env
        amount = 1000 if plan == 'pro' else 2000  # $10.00 and $20.00
        line_item = {
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"Vigia {plan.capitalize()} Plan",
                },
                'unit_amount': amount,
                'recurring': {
                    'interval': 'month',
                },
            },
            'quantity': 1,
        }
    
    try:
        # Create or get customer
        customer_id = org.stripe_customer_id
        if not customer_id:
            customer_kwargs = {'metadata': {'org_id': org.id}}
            # Solo pasamos el email a Stripe si es un email real, no el auto-generado
            if request.user.email and not request.user.email.endswith('@clerk.user'):
                customer_kwargs['email'] = request.user.email
                
            customer = stripe.Customer.create(**customer_kwargs)
            customer_id = customer.id
            org.stripe_customer_id = customer_id
            org.save(update_fields=['stripe_customer_id'])

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='subscription',
            # Critical Rule: Omit payment_method_types to enable dynamic methods
            line_items=[line_item],
            success_url=f"{settings.FRONTEND_URL}/payments/success",
            cancel_url=f"{settings.FRONTEND_URL}/payments/cancel",
            client_reference_id=str(org.id),
            metadata={'plan': plan}
        )
        return Response({'url': session.url})
    except Exception as e:
        return Response({'detail': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_portal_session(request):
    """Create a Stripe Customer Portal session."""
    org = request.user.organization
    if not org or not org.stripe_customer_id:
        return Response({'detail': 'No active billing customer found.'}, status=400)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        kwargs = {
            'customer': org.stripe_customer_id,
            'return_url': request.build_absolute_uri('/') + 'settings',
        }
        if hasattr(settings, 'STRIPE_PORTAL_CONFIG_ID') and settings.STRIPE_PORTAL_CONFIG_ID:
            kwargs['configuration'] = settings.STRIPE_PORTAL_CONFIG_ID
            
        session = stripe.billing_portal.Session.create(**kwargs)
        return Response({'url': session.url})
    except Exception as e:
        return Response({'detail': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """Cancel the current Stripe subscription at period end."""
    org = request.user.organization
    if not org:
        return Response({'detail': 'No organization.'}, status=400)
    
    if not org.stripe_subscription_id:
        # If they don't have a Stripe subscription, just downgrade locally
        org.set_plan('free')
        return Response({'detail': 'Plan downgraded locally.'})

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        # Cancel at period end
        stripe.Subscription.modify(
            org.stripe_subscription_id,
            cancel_at_period_end=True
        )
        # Optional: We keep the plan as ultimate/pro until webhook 'customer.subscription.deleted' 
        # comes through at period end. We can set a local flag if we want, but for now we just 
        # let Stripe handle it. We can return a success message indicating it will cancel later.
        return Response({'detail': 'Suscripción cancelada al final del periodo.'})
    except Exception as e:
        return Response({'detail': str(e)}, status=500)

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        print("Webhook Error: Invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("Webhook Error: Invalid signature")
        return HttpResponse(status=400)

    print(f"Webhook received event type: {event.type}")
    
    try:
        # Handle the event
        if event.type == 'checkout.session.completed':
            session = event.data.object
            org_id = getattr(session, 'client_reference_id', None)
            metadata = getattr(session, 'metadata', {}) or {}
            # Metadata is a StripeObject too, but it behaves like a dict. Let's be safe:
            plan = metadata.get('plan') if hasattr(metadata, 'get') else getattr(metadata, 'plan', None)
            subscription_id = getattr(session, 'subscription', None)
            
            if org_id and plan:
                try:
                    org = Organization.objects.get(id=org_id)
                    org.set_plan(plan)
                    if subscription_id:
                        org.stripe_subscription_id = subscription_id
                        org.save(update_fields=['stripe_subscription_id', 'updated_at'])
                    print(f"Success! Updated org {org_id} to plan {plan}")
                except Organization.DoesNotExist:
                    print(f"Webhook warning: Organization {org_id} not found.")
            else:
                print(f"Webhook warning: Missing org_id ({org_id}) or plan ({plan}) in session.")
                    
        elif event.type == 'customer.subscription.updated':
            subscription = event.data.object
            # Optionally handle subscription cancellations or status changes
            pass

    except Exception as e:
        print(f"Unhandled error in webhook: {e}")
        import traceback
        traceback.print_exc()

    return HttpResponse(status=200)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def llm_config_view(request):
    """Get or update organization LLM config."""
    user = request.user
    if not user.organization:
        return Response({'detail': 'No organization.'}, status=400)
    if user.role != 'admin':
        return Response({'detail': 'Requires admin role.'}, status=403)

    from .models import OrganizationLLMConfig
    from .serializers import OrganizationLLMConfigSerializer

    config, _ = OrganizationLLMConfig.objects.get_or_create(organization=user.organization)

    if request.method == 'GET':
        return Response(OrganizationLLMConfigSerializer(config).data)

    elif request.method == 'PUT':
        serializer = OrganizationLLMConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(OrganizationLLMConfigSerializer(config).data)
        return Response(serializer.errors, status=400)
